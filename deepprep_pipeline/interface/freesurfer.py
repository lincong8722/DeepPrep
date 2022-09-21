from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec, Directory, Str
from run import run_cmd_with_timing, get_freesurfer_threads, multipool
from pathlib import Path

from threading import Thread
import time

class BrainmaskInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subject dir", mandatory=True)
    subject_id = Str(desc="subject id", mandatory=True)
    need_t1 = traits.BaseCBool(desc='bool', mandatory=True)
    nu_file = File(exists=True, desc="mri/nu.mgz", mandatory=True)
    mask_file = File(exists=True, desc="mri/mask.mgz", mandatory=True)

    T1_file = File(exists=False, desc="mri/T1.mgz", mandatory=True)
    brainmask_file = File(exists=False, desc="mri/brainmask.mgz", mandatory=True)
    norm_file = File(exists=False, desc="mri/norm.mgz", mandatory=True)


class BrainmaskOutputSpec(TraitedSpec):
    brainmask_file = File(exists=True, desc="mri/brainmask.mgz")
    norm_file = File(exists=True, desc="mri/norm.mgz")
    T1_file = File(exists=False, desc="mri/T1.mgz")


class Brainmask(BaseInterface):
    input_spec = BrainmaskInputSpec
    output_spec = BrainmaskOutputSpec

    time = 74 / 60  # 运行时间：分钟
    cpu = 1  # 最大cpu占用：个
    gpu = 0  # 最大gpu占用：MB

    def _run_interface(self, runtime):
        # create norm by masking nu 0.7s
        need_t1 = self.inputs.need_t1
        cmd = f'mri_mask {self.inputs.nu_file} {self.inputs.mask_file} {self.inputs.norm_file}'
        run_cmd_with_timing(cmd)

        if need_t1:  # T1.mgz 相比 orig.mgz 更平滑，对比度更高
            # create T1.mgz from nu 96.9s
            cmd = f'mri_normalize -g 1 -mprage {self.inputs.nu_file} {self.inputs.T1_file}'
            run_cmd_with_timing(cmd)

            # create brainmask by masking T1
            cmd = f'mri_mask {self.inputs.T1_file} {self.inputs.mask_file} {self.inputs.brainmask_file}'
            run_cmd_with_timing(cmd)
        else:
            cmd = f'cp {self.inputs.norm_file} {self.inputs.brainmask_file}'
            run_cmd_with_timing(cmd)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["brainmask_file"] = self.inputs.brainmask_file
        outputs["norm_file"] = self.inputs.norm_file
        outputs["T1_file"] = self.inputs.T1_file

        return outputs


class OrigAndRawavgInputSpec(BaseInterfaceInputSpec):
    t1w_files = traits.List(desc='t1w path or t1w paths', mandatory=True)
    subjects_dir = Directory(exists=True, desc='subject dir path', mandatory=True)
    subject_id = Str(desc='subject id', mandatory=True)
    threads = traits.Int(desc='threads')


class OrigAndRawavgOutputSpec(TraitedSpec):
    orig_file = File(exists=True, desc='orig.mgz')
    rawavg_file = File(exists=True, desc='rawavg.mgz')


class OrigAndRawavg(BaseInterface):
    input_spec = OrigAndRawavgInputSpec
    output_spec = OrigAndRawavgOutputSpec

    def __init__(self):
        super(OrigAndRawavg, self).__init__()

    def _run_interface(self, runtime):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)

        files = ' -i '.join(self.inputs.t1w_files)
        cmd = f"recon-all -subject {self.inputs.subject_id} -i {files} -motioncor {fsthreads}"
        run_cmd_with_timing(cmd)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["orig_file"] = Path(f"{self.inputs.subjects_dir}/{self.inputs.subject_id}/mri/orig.mgz")
        outputs['rawavg_file'] = Path(f"{self.inputs.subjects_dir}/{self.inputs.subject_id}/mri/rawavg.mgz")
        return outputs


class FilledInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc='subject dir path', mandatory=True)
    subject_id = Str(desc='subject id', mandatory=True)
    threads = traits.Int(desc='threads')

    aseg_auto_file = File(exists=True, desc='mri/aseg.auto.mgz', mandatory=True)
    norm_file = File(exists=True, desc='mri/norm.mgz', mandatory=True)
    brainmask_file = File(exists=True, desc='mri/brainmask.mgz', mandatory=True)
    talairach_lta = File(exists=True, desc='mri/transforms/talairach.lta', mandatory=True)


class FilledOutputSpec(TraitedSpec):
    aseg_presurf_file = File(exists=True, desc='mri/aseg.presurf.mgz')
    brain_file = File(exists=True, desc='mri/brain.mgz')
    brain_finalsurfs_file = File(exists=True, desc='mri/brain.finalsurfs.mgz')
    wm_file = File(exists=True, desc='mri/wm.mgz')
    wm_filled = File(exists=True, desc='mri/filled.mgz')


class Filled(BaseInterface):
    input_spec = FilledInputSpec
    output_spec = FilledOutputSpec

    time = 249 / 60
    cpu = 3.3
    gpu = 0

    def __init__(self):
        super(Filled, self).__init__()

    def _run_interface(self, runtime):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)

        cmd = f'recon-all -subject {self.inputs.subject_id} -asegmerge {fsthreads}'
        run_cmd_with_timing(cmd)
        cmd = f'recon-all -subject {self.inputs.subject_id} -normalization2 {fsthreads}'
        run_cmd_with_timing(cmd)
        cmd = f'recon-all -subject {self.inputs.subject_id} -maskbfs {fsthreads}'
        run_cmd_with_timing(cmd)
        cmd = f'recon-all -subject {self.inputs.subject_id} -segmentation {fsthreads}'
        run_cmd_with_timing(cmd)
        cmd = f'recon-all -subject {self.inputs.subject_id} -fill {fsthreads}'
        run_cmd_with_timing(cmd)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["aseg_presurf_file"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, 'mri/aseg.presurf.mgz')
        outputs["brain_file"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, 'mri/brain.mgz')
        outputs["brain_finalsurfs_file"] = Path(self.inputs.subjects_dir, self.inputs.subject_id,
                                                'mri/brain.finalsurfs.mgz')
        outputs["wm_file"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, 'mri/wm.mgz')
        outputs["wm_filled"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, 'mri/filled.mgz')
        return outputs


class WhitePreaparc1InputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc='subjects_dir', mandatory=True)
    subject_id = Str(desc="sub-xxx", mandatory=True)
    threads = traits.Int(desc='threads')

    aseg_presurf = File(exists=True, desc="mri/aseg.presurf.mgz", mandatory=True)
    brain_finalsurfs = File(exists=True, desc="mri/brain.finalsurfs.mgz", mandatory=True)
    wm_file = File(exists=True, desc="mri/wm.mgz", mandatory=True)
    filled_file = File(exists=True, desc="mri/filled.mgz", mandatory=True)
    lh_orig = File(exists=True, desc="surf/lh.orig", mandatory=True)
    rh_orig = File(exists=True, desc="surf/rh.orig", mandatory=True)


class WhitePreaparc1OutputSpec(TraitedSpec):
    lh_white_preaparc = File(exists=True, desc="surf/lh.white.preaparc")
    rh_white_preaparc = File(exists=True, desc="surf/rh.white.preaparc")
    lh_curv = File(exists=True, desc="surf/lh.curv")
    rh_curv = File(exists=True, desc="surf/rh.curv")
    lh_area = File(exists=True, desc="surf/lh.area")
    rh_area = File(exists=True, desc="surf/rh.area")
    lh_cortex_label = File(exists=True, desc="label/lh.cortex.label")
    rh_cortex_label = File(exists=True, desc="label/rh.cortex.label")


class WhitePreaparc1(BaseInterface):
    input_spec = WhitePreaparc1InputSpec
    output_spec = WhitePreaparc1OutputSpec

    # Pool
    time = 160 / 60
    cpu = 2.4
    gpu = 0

    def cmd(self, hemi):
        threads = self.inputs.threads if self.inputs.threads else 0
        cmd = f"mris_make_surfaces -aseg aseg.presurf -white white.preaparc -whiteonly -noaparc -mgz -T1 brain.finalsurfs {self.inputs.subject_id} {hemi} threads {threads}"
        run_cmd_with_timing(cmd)

    def _run_interface(self, runtime):
        multipool(self.cmd, Multi_Num=2)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["lh_white_preaparc"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f"surf/lh.white.preaparc")
        outputs["rh_white_preaparc"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f"surf/rh.white.preaparc")
        outputs["lh_curv"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f"surf/lh.curv")
        outputs["rh_curv"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f"surf/rh.curv")
        outputs["lh_area"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f"surf/lh.area")
        outputs["rh_area"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f"surf/rh.area")
        outputs["lh_cortex_label"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f"label/lh.cortex.label")
        outputs["rh_cortex_label"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f"label/rh.cortex.label")

        return outputs


class WhitePreaparc2InputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc='subject dir path', mandatory=True)
    subject_id = Str(desc="sub-xxx", mandatory=True)
    hemi = Str(desc="lh", mandatory=True)
    threads = traits.Int(desc='threads')

    aseg_presurf = File(exists=True, desc="mri/aseg.presurf.mgz", mandatory=True)
    brain_finalsurfs = File(exists=True, desc="mri/brain.finalsurfs.mgz", mandatory=True)
    wm_file = File(exists=True, desc="mri/wm.mgz", mandatory=True)
    filled_file = File(exists=True, desc="mri/filled.mgz", mandatory=True)
    hemi_orig = File(exists=True, desc="surf/?h.orig", mandatory=True)
    hemi_orig_premesh = File(exists=True, desc="surf/?h.orig.premesh", mandatory=True)
    autodet_gw_stats_hemi_dat = File(exists=True, desc="surf/autodet.gw.stats.?h.dat", mandatory=True)
    hemi_white_preaparc = File(exists=True, desc="surf/?h.white.preaparc", mandatory=True)


class WhitePreaparc2OutputSpec(TraitedSpec):
    hemi_white_preaparc = File(exists=True, desc="surf/?h.white.preaparc")
    hemi_curv = File(exists=True, desc="surf/?h.curv")
    hemi_area = File(exists=True, desc="surf/?h.area")
    hemi_cortex_label = File(exists=True, desc="label/?h.cortex.label")


class WhitePreaparc2(BaseInterface):
    input_spec = WhitePreaparc2InputSpec
    output_spec = WhitePreaparc2OutputSpec

    # time = ? / 60
    # cpu = ?
    # gpu = 0

    def _run_interface(self, runtime):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)
        cmd = f'recon-all -subject {self.inputs.subject_id} -hemi {self.inputs.hemi} -autodetgwstats -white-preaparc -cortex-label ' \
              f'-no-isrunning {fsthreads}'
        run_cmd_with_timing(cmd)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["hemi_white_preaparc"] = Path(self.inputs.subjects_dir, self.inputs.subject_id,
                                              f"surf/{self.inputs.hemi}.white.preaparc")
        outputs["hemi_curv"] = Path(self.inputs.subject_dir, self.inputs.subject_id, f"surf/{self.inputs.hemi}.curv")
        outputs["hemi_area"] = Path(self.inputs.subject_dir, self.inputs.subject_id, f"surf/{self.inputs.hemi}.area")
        outputs["hemi_cortex_label"] = Path(self.inputs.subject_dir, self.inputs.subject_id,
                                            f"label/{self.inputs.hemi}.cortex.label")
        return outputs


# class WhitePreaparcInputSpec(BaseInterfaceInputSpec):
#     fswhitepreaparc = traits.Bool(desc="True: mris_make_surfaces; \
#     False: recon-all -autodetgwstats -white-preaparc -cortex-label", mandatory=True)
#     subject = traits.Str(desc="sub-xxx", mandatory=True)
#     hemi = traits.Str(desc="?h", mandatory=True)
#
#     # input files of <mris_make_surfaces>
#     aseg_presurf = File(exists=True, desc="mri/aseg.presurf.mgz")
#     brain_finalsurfs = File(exists=True, desc="mri/brain.finalsurfs.mgz")
#     wm_file = File(exists=True, desc="mri/wm.mgz")
#     filled_file = File(exists=True, desc="mri/filled.mgz")
#     hemi_orig = File(exists=True, desc="surf/?h.orig")
#
#     # input files of <recon-all -autodetgwstats>
#     hemi_orig_premesh = File(exists=True, desc="surf/?h.orig.premesh")
#
#     # input files of <recon-all -white-paraparc>
#     autodet_gw_stats_hemi_dat = File(exists=True, desc="surf/autodet.gw.stats.?h.dat")
#
#     # input files of <recon-all -cortex-label>
#     hemi_white_preaparc = File(exists=True, desc="surf/?h.white.preaparc")
#
#
# class WhitePreaparcOutputSpec(TraitedSpec):
#     # output files of mris_make_surfaces
#     hemi_white_preaparc = File(exists=True, desc="surf/?h.white.preaparc")
#     hemi_curv = File(exists=True, desc="surf/?h.curv")
#     hemi_area = File(exists=True, desc="surf/?h.area")
#     hemi_cortex_label = File(exists=True, desc="label/?h.cortex.label")
#
#
# class WhitePreaparc(BaseInterface):
#     input_spec = WhitePreaparcInputSpec
#     output_spec = WhitePreaparcOutputSpec
#
#     def __init__(self, output_dir: Path, threads: int):
#         super(WhitePreaparc, self).__init__()
#         self.output_dir = output_dir
#         self.threads = threads
#         self.fsthreads = get_freesurfer_threads(threads)
#
#     def _run_interface(self, runtime):
#         if not traits_extension.isdefined(self.inputs.brain_finalsurfs):
#             self.inputs.brain_finalsurfs = self.output_dir / f"{self.inputs.subject}" / "mri/brain.finalsurfs.mgz"
#         if not traits_extension.isdefined(self.inputs.wm_file):
#             self.inputs.wm_file = self.output_dir / f"{self.inputs.subject}" / "mri/wm.mgz"
#
#         if self.inputs.fswhitepreaparc:
#
#
#             if not traits_extension.isdefined(self.inputs.aseg_presurf):
#                 self.inputs.aseg_presurf = self.output_dir / f"{self.inputs.subject}" / "mri/aseg.presurf.mgz"
#             if not traits_extension.isdefined(self.inputs.filled_file):
#                 self.inputs.filled_file = self.output_dir / f"{self.inputs.subject}" / "mri/filled.mgz"
#             if not traits_extension.isdefined(self.inputs.hemi_orig):
#                 self.inputs.hemi_orig = self.output_dir / f"{self.inputs.subject}" / "surf" / f"{self.inputs.hemi}.orig"
#
#             cmd = f'mris_make_surfaces -aseg aseg.presurf -white white.preaparc -whiteonly -noaparc -mgz ' \
#                   f'-T1 brain.finalsurfs {self.inputs.subject} {self.inputs.hemi} threads {self.threads}'
#             run_cmd_with_timing(cmd)
#         else:
#
#
#             if not traits_extension.isdefined(self.inputs.hemi_orig_premesh):
#                 self.inputs.hemi_orig_premesh = self.output_dir / f"{self.inputs.subject}" / f"surf/{self.inputs.hemi}.orig.premesh"
#
#             cmd = f'recon-all -subject {self.inputs.subject} -hemi {self.inputs.hemi} -autodetgwstats -white-preaparc -cortex-label ' \
#                   f'-no-isrunning {self.fsthreads}'
#             run_cmd_with_timing(cmd)
#
#         return runtime
#
#     def _list_outputs(self):
#         outputs = self._outputs().get()
#         outputs["hemi_white_preaparc"] = self.inputs.hemi_white_preaparc
#         outputs["hemi_curv"] = self.output_dir / f"{self.inputs.subject}" / f"surf/{self.inputs.hemi}.curv"
#         outputs["hemi_area"] = self.output_dir / f"{self.inputs.subject}" / f"surf/{self.inputs.hemi}.area"
#         outputs[
#             "hemi_cortex_label"] = self.output_dir / f"{self.inputs.subject}" / f"label/{self.inputs.hemi}.cortex.label"
#         return outputs

class InflatedSphereThresholdInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subject dir", mandatory=True)
    subject_id = traits.String(mandatory=True, desc='sub-xxx')
    threads = traits.Int(desc='threads')
    lh_white_preaparc_file = File(exists=True, desc='surf/lh.white.preaparc')
    rh_white_preaparc_file = File(exists=True, desc='surf/rh.white.preaparc')


class InflatedSphereThresholdOutputSpec(TraitedSpec):
    lh_smoothwm = File(exists=True, desc='surflh.smoothwm')
    rh_smoothwm = File(exists=True, desc='surf/rh.smoothwm')
    lh_inflated = File(exists=True, desc='surf/lh.inflated')
    rh_inflated = File(exists=True, desc='surf/rh.inflated')
    lh_sulc = File(exists=True, desc="surf/lh.sulc")
    rh_sulc = File(exists=True, desc="surf/rh.sulc")
    lh_sphere = File(exists=True, desc="surf/lh.sphere")
    rh_sphere = File(exists=True, desc="surf/rh.sphere")


class InflatedSphere(BaseInterface):
    input_spec = InflatedSphereThresholdInputSpec
    output_spec = InflatedSphereThresholdOutputSpec

    # Pool
    time = 150 / 60  # 运行时间：分钟
    cpu = 6  # 最大cpu占用：个
    gpu = 0  # 最大gpu占用：MB

    def cmd(self, hemi):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)
        # create nicer inflated surface from topo fixed (not needed, just later for visualization)
        cmd = f"recon-all -subject {self.inputs.subject_id} -hemi {hemi} -smooth2 -no-isrunning {fsthreads}"
        run_cmd_with_timing(cmd)

        cmd = f"recon-all -subject {self.inputs.subject_id} -hemi {hemi} -inflate2 -no-isrunning {fsthreads}"
        run_cmd_with_timing(cmd)

        cmd = f"recon-all -subject {self.inputs.subject_id} -hemi {hemi} -sphere -no-isrunning {fsthreads}"
        run_cmd_with_timing(cmd)

    def _run_interface(self, runtime):
        multipool(self.cmd, Multi_Num=2)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['lh_smoothwm'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/lh.smoothwm')
        outputs['rh_smoothwm'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/rh.smoothwm')
        outputs['lh_inflated'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/lh.inflated')
        outputs['rh_inflated'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/rh.inflated')
        outputs['lh_sulc'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/lh.sulc')
        outputs['rh_sulc'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/rh.sulc')
        outputs['lh_sphere'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/lh.sphere')
        outputs['rh_sphere'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/rh.sphere')

        return outputs


class WhitePialThickness1InputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc='subject dir path', mandatory=True)
    subject_id = traits.Str(desc="sub-xxx", mandatory=True)
    threads = traits.Int(desc='threads')

    lh_white_preaparc = File(exists=True, desc="surf/lh.white.preaparc", mandatory=True)
    rh_white_preaparc = File(exists=True, desc="surf/rh.white.preaparc", mandatory=True)
    aseg_presurf = File(exists=True, desc="mri/aseg.presurf.mgz", mandatory=True)
    brain_finalsurfs = File(exists=True, desc="mri/brain.finalsurfs.mgz", mandatory=True)
    wm_file = File(exists=True, desc="mri/wm.mgz", mandatory=True)
    lh_aparc_annot = File(exists=True, desc="label/lh.aparc.annot", mandatory=True)
    rh_aparc_annot = File(exists=True, desc="label/rh.aparc.annot", mandatory=True)
    lh_cortex_hipamyg_label = File(exists=True, desc="label/lh.cortex+hipamyg.label", mandatory=True)
    rh_cortex_hipamyg_label = File(exists=True, desc="label/rh.cortex+hipamyg.label", mandatory=True)
    lh_cortex_label = File(exists=True, desc="label/lh.cortex.label", mandatory=True)
    rh_cortex_label = File(exists=True, desc="label/rh.cortex.label", mandatory=True)

    lh_aparc_DKTatlas_mapped_annot = File(exists=True, desc="label/lh.aparc.DKTatlas.mapped.annot", mandatory=True)
    rh_aparc_DKTatlas_mapped_annot = File(exists=True, desc="label/hh.aparc.DKTatlas.mapped.annot", mandatory=True)
    lh_white = File(exists=True, desc="surf/lh.white", mandatory=True)
    rh_white = File(exists=True, desc="surf/rh.white", mandatory=True)


class WhitePialThickness1OutputSpec(TraitedSpec):
    lh_white = File(exists=True, desc="surf/lh.white")
    rh_white = File(exists=True, desc="surf/rh.white")
    lh_pial_t1 = File(exists=True, desc="surf/lh.pial.T1")
    rh_pial_t1 = File(exists=True, desc="surf/rh.pial.T1")

    lh_pial = File(exists=True, desc="surf/lh.pial")
    rh_pial = File(exists=True, desc="surf/rh.pial")

    lh_curv = File(exists=True, desc="surf/lh.curv")
    rh_curv = File(exists=True, desc="surf/rh.curv")
    lh_area = File(exists=True, desc="surf/lh.area")
    rh_area = File(exists=True, desc="surf/rh.area")
    lh_curv_pial = File(exists=True, desc="surf/lh.curv.pial")
    rh_curv_pial = File(exists=True, desc="surf/rh.curv.pial")
    lh_area_pial = File(exists=True, desc="surf/lh.area.pial")
    rh_area_pial = File(exists=True, desc="surf/rh.area.pial")
    lh_thickness = File(exists=True, desc="surf/lh.thickness")
    rh_thickness = File(exists=True, desc="surf/rh.thickness")


class WhitePialThickness1(BaseInterface):
    # The two methods (WhitePialThickness1 and WhitePialThickness2) are exacly the same.
    input_spec = WhitePialThickness1InputSpec
    output_spec = WhitePialThickness1OutputSpec

    def __init__(self):
        super(WhitePialThickness1, self).__init__()

    def cmd(self, hemi):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)

        cmd = f"recon-all -subject {self.inputs.subject_id} -hemi {hemi} -white " \
              f"-no-isrunning {fsthreads}"
        run_cmd_with_timing(cmd)
        cmd = f"recon-all -subject {self.inputs.subject_id} -hemi {hemi} -pial " \
              f"-no-isrunning {fsthreads}"
        run_cmd_with_timing(cmd)

    def _run_interface(self, runtime):
        # must run surfreg first
        # 20-25 min for traditional surface segmentation (each hemi)
        # this creates aparc and creates pial using aparc, also computes jacobian

        # FreeSurfer 7.2
        # Pool
        time = 242 / 60
        cpu = 6.7
        gpu = 0

        # FreeSurfer 6.0
        # time = (474 + 462) / 60

        multipool(self.cmd, Multi_Num=2)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["lh_white"] = Path(self.inputs.subjects_dir) / self.inputs.subject_id / f"surf/lh.white"
        outputs["rh_white"] = Path(self.inputs.subjects_dir) / self.inputs.subject_id / f"surf/rh.white"
        outputs["lh_pial_t1"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/lh.pial.T1"
        outputs["rh_pial_t1"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/rh.pial.T1"
        outputs["lh_pial"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/lh.pial"
        outputs["rh_pial"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/rh.pial"
        outputs["lh_curv"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/lh.curv"
        outputs["rh_curv"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/rh.curv"
        outputs["lh_area"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/lh.area"
        outputs["rh_area"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/rh.area"
        outputs["lh_curv_pial"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/lh.curv.pial"
        outputs["rh_curv_pial"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/rh.curv.pial"
        outputs["lh_area_pial"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/lh.area.pial"
        outputs["rh_area_pial"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/rh.area.pial"
        outputs["lh_thickness"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/lh.thickness"
        outputs["rh_thickness"] = Path(self.inputs.subjects_dir) / f"{self.inputs.subject_id}" / f"surf/rh.thickness"

        return outputs


class WhitePialThickness2InputSpec(BaseInterfaceInputSpec):
    subject = traits.Str(desc="sub-xxx", mandatory=True)
    hemi = traits.Str(desc="lh", mandatory=True)

    autodet_gw_stats_hemi_dat = File(exists=True, desc="surf/autodet.gw.stats.?h.dat", mandatory=True)
    aseg_presurf = File(exists=True, desc="mri/aseg.presurf.mgz", mandatory=True)
    wm_file = File(exists=True, desc="mri/wm.mgz", mandatory=True)
    brain_finalsurfs = File(exists=True, desc="mri/brain.finalsurfs.mgz", mandatory=True)
    hemi_white_preaparc = File(exists=True, desc="surf/?h.white.preaparc", mandatory=True)
    hemi_white = File(exists=True, desc="surf/?h.white", mandatory=True)
    hemi_cortex_label = File(exists=True, desc="label/?h.cortex.label", mandatory=True)
    hemi_aparc_DKTatlas_mapped_annot = File(exists=True, desc="label/?h.aparc.DKTatlas.mapped.annot", mandatory=True)

    hemi_pial_t1 = File(exists=True, desc="surf/?h.pial.T1", mandatory=True)


class WhitePialThickness2OutputSpec(TraitedSpec):
    hemi_white = File(exists=True, desc="surf/?h.white")
    hemi_pial_t1 = File(exists=True, desc="surf/?h.pial.T1")

    hemi_pial = File(exists=True, desc="surf/?h.pial")

    hemi_curv = File(exists=True, desc="surf/?h.curv")
    hemi_area = File(exists=True, desc="surf/?h.area")
    hemi_curv_pial = File(exists=True, desc="surf/?h.curv.pial")
    hemi_area_pial = File(exists=True, desc="surf/?h.area.pial")
    hemi_thickness = File(exists=True, desc="surf/?h.thickness")


class WhitePialThickness2(BaseInterface):
    # The two methods (WhitePialThickness1 and WhitePialThickness2) are exacly same.
    input_spec = WhitePialThickness1InputSpec
    output_spec = WhitePialThickness1OutputSpec

    def __init__(self, output_dir: Path, threads: int):
        super(WhitePialThickness2, self).__init__()
        self.output_dir = output_dir
        self.threads = threads
        self.fsthreads = get_freesurfer_threads(threads)

    def _run_interface(self, runtime):
        # The two methods below are exacly same.
        # 4 min compute white :
        time = 330 / 60
        cpu = 1
        gpu = 0

        cmd = f"mris_place_surface --adgws-in {self.inputs.autodet_gw_stats_hemi_dat} " \
              f"--seg {self.inputs.aseg_presurf} --wm {self.inputs.wm_file} --invol {self.inputs.brain_finalsurfs} --{self.inputs.hemi} " \
              f"--i {self.inputs.hemi_white_preaparc} --o {self.inputs.hemi_white} --white --nsmooth 0 " \
              f"--rip-label {self.inputs.hemi_cortex_label} --rip-bg --rip-surf {self.inputs.hemi_white_preaparc} " \
              f"--aparc {self.inputs.hemi_aparc_DKTatlas_mapped_annot}"
        run_cmd_with_timing(cmd)
        # 4 min compute pial :
        cmd = f"mris_place_surface --adgws-in {self.inputs.autodet_gw_stats_hemi_dat} --seg {self.inputs.aseg_presurf} " \
              f"--wm {self.inputs.wm_file} --invol {self.inputs.brain_finalsurfs} --{self.inputs.hemi} --i {self.inputs.hemi_white} " \
              f"--o {self.inputs.hemi_pial_t1} --pial --nsmooth 0 --rip-label {self.inputs.hemi_cortexhipamyg_label} " \
              f"--pin-medial-wall {self.inputs.hemi_cortex_label} --aparc {self.inputs.hemi_aparc_DKTatlas_mapped_annot} " \
              f"--repulse-surf {self.inputs.hemi_white} --white-surf {self.inputs.hemi_white}"
        run_cmd_with_timing(cmd)

        # Here insert DoT2Pial  later --> if T2pial is not run, need to softlink pial.T1 to pial!

        cmd = f"cp {self.inputs.hemi_pial_t1} {self.inputs.hemi_pial}"
        run_cmd_with_timing(cmd)

        # these are run automatically in fs7* recon-all and
        # cannot be called directly without -pial flag (or other t2 flags)
        cmd = f"mris_place_surface --curv-map {self.inputs.hemi_white} 2 10 {self.inputs.hemi_curv}"
        run_cmd_with_timing(cmd)
        cmd = f"mris_place_surface --area-map {self.inputs.hemi_white} {self.inputs.hemi_area}"
        run_cmd_with_timing(cmd)
        cmd = f"mris_place_surface --curv-map {self.inputs.hemi_pial} 2 10 {self.inputs.hemi_curv_pial}"
        run_cmd_with_timing(cmd)
        cmd = f"mris_place_surface --area-map {self.inputs.hemi_pial} {self.inputs.hemi_area_pial}"
        run_cmd_with_timing(cmd)
        cmd = f" mris_place_surface --thickness {self.inputs.hemi_white} {self.inputs.hemi_pial} " \
              f"20 5 {self.inputs.hemi_thickness}"
        run_cmd_with_timing(cmd)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["hemi_white"] = self.output_dir / f"{self.inputs.subject}" / f"surf/{self.inputs.hemi}.white"
        outputs["hemi_pial_t1"] = self.output_dir / f"{self.inputs.subject}" / f"surf/{self.inputs.hemi}.pial.T1"
        outputs["hemi_pial"] = self.output_dir / f"{self.inputs.subject}" / f"surf/{self.inputs.hemi}.pial"
        outputs["hemi_curv"] = self.output_dir / f"{self.inputs.subject}" / f"surf/{self.inputs.hemi}.curv"
        outputs["hemi_area"] = self.output_dir / f"{self.inputs.subject}" / f"surf/{self.inputs.hemi}.area"
        outputs["hemi_curv_pial"] = self.output_dir / f"{self.inputs.subject}" / f"surf/{self.inputs.hemi}.curv.pial"
        outputs["hemi_area_pial"] = self.output_dir / f"{self.inputs.subject}" / f"surf/{self.inputs.hemi}.area.pial"
        outputs["hemi_thickness"] = self.output_dir / f"{self.inputs.subject}" / f"surf/{self.inputs.hemi}.thickness"

        return outputs


class CurvstatsInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subjects dir", mandatory=True)
    subject_id = Str(desc="sub-xxx", mandatory=True)

    lh_smoothwm = File(exists=True, desc="surf/lh.smoothwm", mandatory=True)
    rh_smoothwm = File(exists=True, desc="surf/rh.smoothwm", mandatory=True)
    lh_curv = File(exists=True, desc="surf/lh.curv", mandatory=True)
    rh_curv = File(exists=True, desc="surf/rh.curv", mandatory=True)
    lh_sulc = File(exists=True, desc="surf/lh.sulc", mandatory=True)
    rh_sulc = File(exists=True, desc="surf/rh.sulc", mandatory=True)
    threads = traits.Int(desc='threads')


class CurvstatsOutputSpec(TraitedSpec):
    lh_curv_stats = File(exists=True, desc="stats/lh.curv.stats")
    rh_curv_stats = File(exists=True, desc="stats/rh.curv.stats")


class Curvstats(BaseInterface):
    input_spec = CurvstatsInputSpec
    output_spec = CurvstatsOutputSpec

    # Pool
    time = 2.7 / 60  # 运行时间：分钟 / 单脑测试时间
    cpu = 2.7  # 最大cpu占用：个
    gpu = 0  # 最大gpu占用：MB

    def cmd(self, hemi):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)

        # in FS7 curvstats moves here
        cmd = f"recon-all -subject {self.inputs.subject_id} -hemi {hemi} -curvstats -no-isrunning {fsthreads}"
        run_cmd_with_timing(cmd)

    def _run_interface(self, runtime):
        multipool(self.cmd, Multi_Num=2)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["lh_curv_stats"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'stats/lh.curv.stats')
        outputs["rh_curv_stats"] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'stats/rh.curv.stats')

        return outputs


class CortribbonInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subjects dir", mandatory=True)
    subject_id = Str(desc="sub-xxx", mandatory=True)
    threads = traits.Int(desc='threads')

    aseg_presurf_file = File(exists=True, desc="mri/aseg.presurf.mgz", mandatory=True)
    lh_white = File(exists=True, desc="surf/lh.white", mandatory=True)
    rh_white = File(exists=True, desc="surf/rh.white", mandatory=True)
    lh_pial = File(exists=True, desc="surf/lh.pial", mandatory=True)
    rh_pial = File(exists=True, desc="surf/rh.pial", mandatory=True)

    lh_ribbon = File(exists=False, desc="mri/lh.ribbon.mgz", mandatory=True)
    rh_ribbon = File(exists=False, desc="mri/rh.ribbon.mgz", mandatory=True)
    ribbon = File(exists=False, desc="mri/ribbon.mgz", mandatory=True)


class CortribbonOutputSpec(TraitedSpec):
    lh_ribbon = File(exists=True, desc="mri/lh.ribbon.mgz")
    rh_ribbon = File(exists=True, desc="mri/rh.ribbon.mgz")
    ribbon = File(exists=True, desc="mri/ribbon.mgz")


class Cortribbon(BaseInterface):
    input_spec = CortribbonInputSpec
    output_spec = CortribbonOutputSpec

    time = 203 / 60  # 运行时间：分钟 /
    cpu = 3.5  # 最大cpu占用：个
    gpu = 0  # 最大gpu占用：MB

    def _run_interface(self, runtime):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)
        # -cortribbon 4 minutes, ribbon is used in mris_anatomical stats
        # to remove voxels from surface based volumes that should not be cortex
        # anatomical stats can run without ribon, but will omit some surface based measures then
        # wmparc needs ribbon, probably other stuff (aparc to aseg etc).
        # could be stripped but lets run it to have these measures below
        cmd = f"recon-all -subject {self.inputs.subject_id} -cortribbon {fsthreads}"
        run_cmd_with_timing(cmd)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["lh_ribbon"] = self.inputs.lh_ribbon
        outputs["rh_ribbon"] = self.inputs.rh_ribbon
        outputs["ribbon"] = self.inputs.ribbon

        return outputs


class ParcstatsInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subjects dir", mandatory=True)
    subject_id = Str(desc="sub-xxx", mandatory=True)
    threads = traits.Int(desc='threads')

    lh_aparc_annot = File(exists=True, desc="label/lh.aparc.annot", mandatory=True)
    rh_aparc_annot = File(exists=True, desc="label/rh.aparc.annot", mandatory=True)
    wm_file = File(exists=True, desc="mri/wm.mgz", mandatory=True)
    aseg_file = File(exists=True, desc="mri/aseg.mgz", mandatory=True)
    ribbon_file = File(exists=True, desc="mri/ribbon.mgz", mandatory=True)
    lh_white = File(exists=True, desc="surf/lh.white", mandatory=True)
    rh_white = File(exists=True, desc="surf/rh.white", mandatory=True)
    lh_pial = File(exists=True, desc="surf/lh.pial", mandatory=True)
    rh_pial = File(exists=True, desc="surf/rh.pial", mandatory=True)
    lh_thickness = File(exists=True, desc="surf/lh.thickness", mandatory=True)
    rh_thickness = File(exists=True, desc="surf/rh.thickness", mandatory=True)

    lh_aparc_stats = File(exists=False, desc="stats/lh.aparc.stats", mandatory=True)
    rh_aparc_stats = File(exists=False, desc="stats/rh.aparc.stats", mandatory=True)
    lh_aparc_pial_stats = File(exists=False, desc="stats/lh.aparc.pial.stats", mandatory=True)
    rh_aparc_pial_stats = File(exists=False, desc="stats/rh.aparc.pial.stats", mandatory=True)
    aparc_annot_ctab = File(exists=False, desc="label/aparc.annot.ctab", mandatory=True)


class ParcstatsOutputSpec(TraitedSpec):
    lh_aparc_stats = File(exists=True, desc="stats/lh.aparc.stats")
    rh_aparc_stats = File(exists=True, desc="stats/rh.aparc.stats")
    lh_aparc_pial_stats = File(exists=True, desc="stats/lh.aparc.pial.stats")
    rh_aparc_pial_stats = File(exists=True, desc="stats/rh.aparc.pial.stats")
    aparc_annot_ctab = File(exists=True, desc="label/aparc.annot.ctab")


class Parcstats(BaseInterface):
    input_spec = ParcstatsInputSpec
    output_spec = ParcstatsOutputSpec

    time = 91 / 60  # 运行时间：分钟 /
    cpu = 3  # 最大cpu占用：个
    gpu = 0  # 最大gpu占用：MB

    def _run_interface(self, runtime):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)

        cmd = f"recon-all -subject {self.inputs.subject_id} -parcstats {fsthreads}"
        run_cmd_with_timing(cmd)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["lh_aparc_stats"] = self.inputs.lh_aparc_stats
        outputs["rh_aparc_stats"] = self.inputs.rh_aparc_stats
        outputs["lh_aparc_pial_stats"] = self.inputs.lh_aparc_pial_stats
        outputs["rh_aparc_pial_stats"] = self.inputs.rh_aparc_pial_stats
        outputs["aparc_annot_ctab"] = self.inputs.aparc_annot_ctab

        return outputs


class PctsurfconInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subjects dir", mandatory=True)
    subject_id = Str(desc="sub-xxx", mandatory=True)
    threads = traits.Int(desc='threads')
    rawavg_file = File(exists=True, desc="mri/rawavg.mgz", mandatory=True)
    orig_file = File(exists=True, desc="mri/orig.mgz", mandatory=True)
    lh_cortex_label = File(exists=True, desc="label/lh.cortex.label", mandatory=True)
    rh_cortex_label = File(exists=True, desc="label/rh.cortex.label", mandatory=True)
    lh_white = File(exists=True, desc="surf/lh.white", mandatory=True)
    rh_white = File(exists=True, desc="surf/rh.white", mandatory=True)

    lh_wg_pct_mgh = File(exists=False, desc="surf/lh.w-g.pct.mgh", mandatory=True)
    rh_wg_pct_mgh = File(exists=False, desc="surf/rh.w-g.pct.mgh", mandatory=True)
    lh_wg_pct_stats = File(exists=False, desc="stats/lh.w-g.pct.stats", mandatory=True)
    rh_wg_pct_stats = File(exists=False, desc="stats/rh.w-g.pct.stats", mandatory=True)


class PctsurfconOutputSpec(TraitedSpec):
    lh_wg_pct_mgh = File(exists=True, desc="surf/lh.w-g.pct.mgh")
    rh_wg_pct_mgh = File(exists=True, desc="surf/rh.w-g.pct.mgh")
    lh_wg_pct_stats = File(exists=True, desc="stats/lh.w-g.pct.stats")
    rh_wg_pct_stats = File(exists=True, desc="stats/rh.w-g.pct.stats")


class Pctsurfcon(BaseInterface):
    input_spec = PctsurfconInputSpec
    output_spec = PctsurfconOutputSpec

    time = 9 / 60  # 运行时间：分钟 /
    cpu = 2  # 最大cpu占用：个
    gpu = 0  # 最大gpu占用：MB

    def _run_interface(self, runtime):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)

        cmd = f"recon-all -subject {self.inputs.subject_id} -pctsurfcon {fsthreads}"
        run_cmd_with_timing(cmd)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["lh_wg_pct_mgh"] = self.inputs.subjects_dir / self.inputs.subject_id / 'surf' / f'lh.w-g.pct.mgh'
        outputs["rh_wg_pct_mgh"] = self.inputs.subjects_dir / self.inputs.subject_id / 'surf' / f'rh.w-g.pct.mgh'
        outputs["lh_wg_pct_stats"] = self.inputs.subjects_dir / self.inputs.subject_id / 'stats' / 'lh.w-g.pct.stats'
        outputs["rh_wg_pct_stats"] = self.inputs.subjects_dir / self.inputs.subject_id / 'stats' / 'rh.w-g.pct.stats'

        return outputs


class HyporelabelInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subjects dir", mandatory=True)
    subject_id = Str(desc="subject id", mandatory=True)
    threads = traits.Int(desc='threads')
    aseg_presurf = File(exists=True, desc="mri/aseg.presurf.mgz", mandatory=True)
    lh_white = File(exists=True, desc="surf/lh.white", mandatory=True)
    rh_white = File(exists=True, desc="surf/rh.white", mandatory=True)

    aseg_presurf_hypos = File(exists=False, desc="mri/aseg.presurf.hypos.mgz", mandatory=True)


class HyporelabelOutputSpec(TraitedSpec):
    aseg_presurf_hypos = File(exists=True, desc="mri/aseg.presurf.hypos.mgz")


class Hyporelabel(BaseInterface):
    input_spec = HyporelabelInputSpec
    output_spec = HyporelabelOutputSpec

    # Pool
    time = 9 / 60  # 运行时间：分钟 / 单脑测试时间
    cpu = 2.3  # 最大cpu占用：个
    gpu = 0  # 最大gpu占用：MB

    def _run_interface(self, runtime):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)

        cmd = f"recon-all -subject {self.inputs.subject_id} -hyporelabel {fsthreads}"
        run_cmd_with_timing(cmd)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["aseg_presurf_hypos"] = self.inputs.aseg_presurf_hypos

        return outputs


class JacobianAvgcurvCortparcThresholdInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subjects dir", mandatory=True)
    subject_id = traits.Str(mandatory=True, desc='sub-xxx')
    lh_white_preaparc = File(exists=True, mandatory=True, desc='surf/lh.white.preaparc')
    rh_white_preaparc = File(exists=True, mandatory=True, desc='surf/rh.white.preaparc')
    lh_sphere_reg = File(exists=True, mandatory=True, desc='surf/lh.sphere.reg')
    rh_sphere_reg = File(exists=True, mandatory=True, desc='surf/rh.sphere.reg')
    lh_jacobian_white = File(mandatory=True, desc='surf/lh.jacobian_white')
    rh_jacobian_white = File(mandatory=True, desc='surf/rh.jacobian_white')
    lh_avg_curv = File(mandatory=True, desc='surf/lh.avg_curv')  # Do not set exists=True !!
    rh_avg_curv = File(mandatory=True, desc='surf/rh.avg_curv')  # Do not set exists=True !!
    aseg_presurf_file = File(exists=True, mandatory=True, desc="mri/aseg.presurf.mgz")
    lh_cortex_label = File(exists=True, mandatory=True, desc="label/lh.cortex.label")
    rh_cortex_label = File(exists=True, mandatory=True, desc="label/rh.cortex.label")

    lh_aparc_annot = File(mandatory=True, desc="label/lh.aparc.annot")
    rh_aparc_annot = File(mandatory=True, desc="label/rh.aparc.annot")
    threads = traits.Int(desc='threads')


class JacobianAvgcurvCortparcThresholdOutputSpec(TraitedSpec):
    lh_jacobian_white = File(exists=True, desc='surf/lh.jacobian_white')
    rh_jacobian_white = File(exists=True, desc='surf/rh.jacobian_white')
    lh_avg_curv = File(exists=True, desc='surf/lh.avg_curv')  # Do not set exists=True !!
    rh_avg_curv = File(exists=True, desc='surf/rh.avg_curv')  # Do not set exists=True !!
    lh_aparc_annot = File(exists=True, desc="surf/lh.aparc.annot")
    rh_aparc_annot = File(exists=True, desc="surf/rh.aparc.annot")


class JacobianAvgcurvCortparc(BaseInterface):
    input_spec = JacobianAvgcurvCortparcThresholdInputSpec
    output_spec = JacobianAvgcurvCortparcThresholdOutputSpec

    # time = 28 / 60  # 运行时间：分钟
    # cpu = 3  # 最大cpu占用：个
    # gpu = 0  # 最大gpu占用：MB

    def cmd(self, hemi):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)
        # create nicer inflated surface from topo fixed (not needed, just later for visualization)
        cmd = f"recon-all -subject {self.inputs.subject_id} -hemi {hemi} -jacobian_white -avgcurv -cortparc " \
              f"-no-isrunning {fsthreads}"
        run_cmd_with_timing(cmd)

    def _run_interface(self, runtime):
        multipool(self.cmd, Multi_Num=2)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['lh_jacobian_white'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/lh.jacobian_white')
        outputs['rh_jacobian_white'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/rh.jacobian_white')
        outputs['lh_avg_curv'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/lh.avg_curv')
        outputs['rh_avg_curv'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'surf/rh.avg_curv')
        outputs['lh_aparc_annot'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'label/lh.aparc.annot')
        outputs['rh_aparc_annot'] = Path(self.inputs.subjects_dir, self.inputs.subject_id, f'label/rh.aparc.annot')

        return outputs


class SegstatsInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subject dir", mandatory=True)
    subject_id = Str(desc="subject id", mandatory=True)
    threads = traits.Int(desc='threads')
    hemi = Str(desc="lh/rh", mandatory=True)
    brainmask_file = File(exists=True, desc="mri/brainmask.mgz", mandatory=True)
    norm_file = File(exists=True, desc="mri/norm.mgz", mandatory=True)
    aseg_file = File(exists=True, desc="mri/aseg.mgz", mandatory=True)
    aseg_presurf_file = File(exists=True, desc="mri/aseg.presurf.mgz", mandatory=True)
    ribbon_file = File(exists=True, desc="mri/ribbon.mgz", mandatory=True)
    hemi_orig_nofix_file = File(exists=True, desc="surf/?h.orig.nofix", mandatory=True)
    hemi_white_file = File(exists=True, desc="surf/?h.white", mandatory=True)
    hemi_pial_file = File(exists=True, desc="surf/?h.pial", mandatory=True)

    aseg_stats_file = File(exists=False, desc="stats/aseg.stats", mandatory=True)


class SegstatsOutputSpec(TraitedSpec):
    aseg_stats_file = File(exists=True, desc="stats/aseg.stats")


class Segstats(BaseInterface):
    input_spec = SegstatsInputSpec
    output_spec = SegstatsOutputSpec

    time = 34 / 60  # 运行时间：分钟 / 单脑测试时间
    cpu = 8  # 最大cpu占用：个
    gpu = 0  # 最大gpu占用：MB

    def _run_interface(self, runtime):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)

        cmd = f"recon-all -subject {self.inputs.subject_id} -segstats  {fsthreads}"
        run_cmd_with_timing(cmd)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['aseg_stats_file'] = self.inputs.aseg_stats_file

        return outputs


class Aseg7InputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subjects dir", mandatory=True)
    subject_id = Str(desc="sub-xxx", mandatory=True)
    subject_mri_dir = Directory(exists=True, desc="subject mri dir", mandatory=True)
    threads = traits.Int(desc='threads')

    aseg_presurf_hypos = File(exists=False, desc="mri/aseg.presurf.hypos.mgz", mandatory=True)
    # ribbon_file = File(exists=True, desc="mri/ribbon.mgz", mandatory=True)
    lh_cortex_label = File(exists=True, desc="label/lh.cortex.label", mandatory=True)
    lh_white = File(exists=True, desc="surf/lh.white", mandatory=True)
    lh_pial = File(exists=True, desc="surf/lh.pial", mandatory=True)
    rh_cortex_label = File(exists=True, desc="label/rh.cortex.label", mandatory=True)
    rh_white = File(exists=True, desc="surf/rh.white", mandatory=True)
    rh_pial = File(exists=True, desc="surf/rh.pial", mandatory=True)
    lh_aparc_annot = File(exists=True, desc="surf/lh.aparc.annot", mandatory=True)
    rh_aparc_annot = File(exists=True, desc="surf/rh.aparc.annot", mandatory=True)

    aparc_aseg = File(exists=False, desc="mri/aparc+aseg.mgz", mandatory=True)


class Aseg7OutputSpec(TraitedSpec):
    aparc_aseg = File(exists=True, desc="mri/aparc+aseg.mgz")


class Aseg7(BaseInterface):
    input_spec = Aseg7InputSpec
    output_spec = Aseg7OutputSpec

    time = 45 / 60  # 运行时间：分钟 / 单脑测试时间
    cpu = 5.6  # 最大cpu占用：个
    gpu = 0  # 最大gpu占用：MB

    def _run_interface(self, runtime):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)
        cmd = f'mri_surf2volseg --o aparc+aseg.mgz --label-cortex --i aseg.mgz ' \
              f'--threads {threads} ' \
              f'--lh-annot {self.inputs.lh_aparc_annot } 1000 ' \
              f'--lh-cortex-mask {self.inputs.lh_cortex_label } --lh-white {self.inputs.lh_white } ' \
              f'--lh-pial {self.inputs.lh_pial } --rh-annot {self.inputs.rh_aparc_annot } 2000 ' \
              f'--rh-cortex-mask {self.inputs.rh_cortex_label } --rh-white {self.inputs.rh_white } ' \
              f'--rh-pial {self.inputs.rh_pial } '
        run_cmd_with_timing(cmd)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["aparc_aseg "] = self.inputs.aparc_aseg
        return outputs


class Aseg7ToAsegInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subjects dir", mandatory=True)
    subject_id = Str(desc="sub-xxx", mandatory=True)
    threads = traits.Int(desc='threads')

    # aseg_presurf_hypos  = File(exists=True, desc="mri/aseg.presurf.hypos.mgz", mandatory=True)
    # ribbon_file = File(exists=True, desc="mri/ribbon.mgz", mandatory=True)
    lh_cortex_label = File(exists=True, desc="label/lh.cortex.label", mandatory=True)
    lh_white = File(exists=True, desc="surf/lh.white", mandatory=True)
    lh_pial = File(exists=True, desc="surf/lh.pial", mandatory=True)
    rh_cortex_label = File(exists=True, desc="label/rh.cortex.label", mandatory=True)
    rh_white = File(exists=True, desc="surf/rh.white", mandatory=True)
    rh_pial = File(exists=True, desc="surf/rh.pial", mandatory=True)

    aseg_file = File(exists=False, desc="mri/aseg.mgz", mandatory=True)


class Aseg7ToAsegOutputSpec(TraitedSpec):
    aseg_file = File(exists=True, desc="mri/aseg.mgz")


class Aseg7ToAseg(BaseInterface):
    input_spec = Aseg7ToAsegInputSpec
    output_spec = Aseg7ToAsegOutputSpec

    time = 16 / 60  # 运行时间：分钟 / 单脑测试时间
    cpu = 1.6  # 最大cpu占用：个
    gpu = 0  # 最大gpu占用：MB

    def _run_interface(self, runtime):
        threads = self.inputs.threads if self.inputs.threads else 0
        fsthreads = get_freesurfer_threads(threads)

        cmd = f"recon-all -subject {self.inputs.subject_id} -hyporelabel -apas2aseg {fsthreads}"
        run_cmd_with_timing(cmd)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["aseg_file"] = self.inputs.aseg_file

        return outputs


class BalabelsMultInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(exists=True, desc="subject dir", mandatory=True)
    lh_sphere_reg = File(exists=True, desc="surf/lh.sphere.reg", mandatory=True)
    rh_sphere_reg = File(exists=True, desc="surf/rh.sphere.reg", mandatory=True)
    subject_id = Str(desc="subject id", mandatory=True)
    threads = traits.Int(desc='threads')
    freesurfer_dir = Directory(exists=True, desc="freesurfer dir", mandatory=True)
    fsaverage_label_dir = Directory(exists=True, desc="fsaverage label dir", mandatory=True)
    # sub_label_dir = Directory(exists=True, desc="sub label dir", mandatory=True)
    # sub_stats_dir = Directory(exists=True, desc="sub stats dir", mandatory=True)

    lh_BA45_exvivo = File(exists=False, desc="label/lh.BA45_exvivo.label", mandatory=True)
    rh_BA45_exvivo = File(exists=False, desc="label/rh.BA45_exvivo.label", mandatory=True)
    lh_perirhinal_exvivo = File(exists=False, desc="label/lh.perirhinal_exvivo.label", mandatory=True)
    rh_perirhinal_exvivo = File(exists=False, desc="label/rh.perirhinal_exvivo.label", mandatory=True)
    lh_entorhinal_exvivo = File(exists=False, desc="label/lh.entorhinal_exvivo.label", mandatory=True)
    rh_entorhinal_exvivo = File(exists=False, desc="label/rh.entorhinal_exvivo.label", mandatory=True)
    BA_exvivo_thresh = File(exists=False, desc="label/BA_exvivo.thresh.ctab", mandatory=True)

class BalabelsMultOutputSpec(TraitedSpec):
    lh_BA45_exvivo = File(exists=True, desc="label/lh.BA45_exvivo.label")
    rh_BA45_exvivo = File(exists=True, desc="label/rh.BA45_exvivo.label")
    lh_perirhinal_exvivo = File(exists=True, desc="label/lh.perirhinal_exvivo.label")
    rh_perirhinal_exvivo = File(exists=True, desc="label/rh.perirhinal_exvivo.label")
    lh_entorhinal_exvivo = File(exists=True, desc="label/lh.entorhinal_exvivo.label")
    rh_entorhinal_exvivo = File(exists=True, desc="label/rh.entorhinal_exvivo.label")
    BA_exvivo_thresh = File(exists=True, desc="label/BA_exvivo.thresh.ctab")

class BalabelsMult(BaseInterface):
    input_spec = BalabelsMultInputSpec
    output_spec = BalabelsMultOutputSpec

    time = 44.8 / 60  # 运行时间：分钟 / 单脑测试时间
    cpu = 1  # 最大cpu占用：个
    gpu = 0  # 最大gpu占用：MB

    def __init__(self):
        super(BalabelsMult, self).__init__()


    def cmd(self, hemi):
        threads = self.inputs.threads if self.inputs.threads else 0
        sub_label_dir = Path(self.inputs.subjects_dir, self.inputs.subject_id, 'label')
        sub_stats_dir = Path(self.inputs.subjects_dir, self.inputs.subject_id, 'stats')

        file_names = ['BA1_exvivo.label', 'BA2_exvivo.label','BA3a_exvivo.label', 'BA3b_exvivo.label', 'BA4a_exvivo.label',
                     'BA4p_exvivo.label', 'BA6_exvivo.label', 'BA44_exvivo.label', 'BA45_exvivo.label', 'V1_exvivo.label',
                     'V2_exvivo.label', 'MT_exvivo.label', 'entorhinal_exvivo.label', 'perirhinal_exvivo.label', 'FG1.mpm.vpnl.label',
                     'FG2.mpm.vpnl.label', 'FG3.mpm.vpnl.label', 'FG4.mpm.vpnl.label', 'hOc1.mpm.vpnl.label', 'hOc2.mpm.vpnl.label',
                     'hOc3v.mpm.vpnl.label', 'hOc4v.mpm.vpnl.label']
        def multi_process(file_names,Run):
            all_num = len(file_names)
            num_per_thread = all_num // threads
            thread_pool = []
            for i in range(threads):
                if i == threads - 1:
                    t = Thread(target=Run, args=(file_names[i * num_per_thread:],))
                else:
                    start = i * num_per_thread
                    end = (i + 1) * num_per_thread
                    t = Thread(target=Run, args=(file_names[start:end],))
                thread_pool.append(t)
            t1 = time.time()
            for num, i in enumerate(thread_pool):
                print("thread", num, "start")
                i.start()
            for i in thread_pool:
                i.join()
            t2 = time.time()
            print("time:", t2 - t1)
        def Run_1(file_name):
            for i in range(len(file_name)):
                cmd = f"mri_label2label --srcsubject fsaverage --srclabel {self.inputs.fsaverage_label_dir}/{hemi}.{file_name[i]} " \
                      f"--trgsubject {self.inputs.subject_id} --trglabel {sub_label_dir}/{hemi}.{file_name[i]} " \
                      f"--hemi {hemi} --regmethod surface"
                run_cmd_with_timing(cmd)

        multi_process(file_names,Run_1)

        cmd = f'mris_label2annot --s {self.inputs.subject_id} --ctab {self.inputs.freesurfer_dir}/average/colortable_vpnl.txt --hemi {hemi} ' \
              f'--a mpm.vpnl --maxstatwinner --noverbose --l {sub_label_dir}/{hemi}.FG1.mpm.vpnl.label ' \
              f'--l {sub_label_dir}/{hemi}.FG2.mpm.vpnl.label --l {sub_label_dir}/{hemi}.FG3.mpm.vpnl.label ' \
              f'--l {sub_label_dir}/{hemi}.FG4.mpm.vpnl.label --l {sub_label_dir}/{hemi}.hOc1.mpm.vpnl.label ' \
              f'--l {sub_label_dir}/{hemi}.hOc2.mpm.vpnl.label --l {sub_label_dir}/{hemi}.hOc3v.mpm.vpnl.label ' \
              f'--l {sub_label_dir}/{hemi}.hOc4v.mpm.vpnl.label'
        run_cmd_with_timing(cmd)

        part_file_names = ['BA1_exvivo.thresh.label', 'BA2_exvivo.thresh.label','BA3a_exvivo.thresh.label', 'BA3b_exvivo.thresh.label', 'BA4a_exvivo.thresh.label',
                     'BA4p_exvivo.thresh.label', 'BA6_exvivo.thresh.label', 'BA44_exvivo.thresh.label', 'BA45_exvivo.thresh.label', 'V1_exvivo.thresh.label',
                     'V2_exvivo.thresh.label', 'MT_exvivo.thresh.label', 'entorhinal_exvivo.thresh.label', 'perirhinal_exvivo.thresh.label']

        def Run_2(part_file_name):
            for i in range(len(part_file_name)):
                cmd = f"mri_label2label --srcsubject fsaverage --srclabel {self.inputs.fsaverage_label_dir}/{hemi}.{part_file_name[i]} " \
                      f"--trgsubject {self.inputs.subject_id} --trglabel {sub_label_dir}/{hemi}.{part_file_name[i]} " \
                      f"--hemi {hemi} --regmethod surface"
                run_cmd_with_timing(cmd)

        multi_process(part_file_names,Run_2)
        cmd = f'mris_label2annot --s {self.inputs.subject_id} --hemi {hemi} --ctab {self.inputs.freesurfer_dir}/average/colortable_BA.txt --l {hemi}.BA1_exvivo.label ' \
              f'--l {hemi}.BA2_exvivo.label --l {hemi}.BA3a_exvivo.label --l {hemi}.BA3b_exvivo.label --l {hemi}.BA4a_exvivo.label ' \
              f'--l {hemi}.BA4p_exvivo.label --l {hemi}.BA6_exvivo.label --l {hemi}.BA44_exvivo.label --l {hemi}.BA45_exvivo.label ' \
              f'--l {hemi}.V1_exvivo.label --l {hemi}.V2_exvivo.label --l {hemi}.MT_exvivo.label --l {hemi}.perirhinal_exvivo.label ' \
              f'--l {hemi}.entorhinal_exvivo.label --a BA_exvivo --maxstatwinner --noverbose'
        run_cmd_with_timing(cmd)
        cmd = f'mris_label2annot --s {self.inputs.subject_id} --hemi {hemi} --ctab {self.inputs.freesurfer_dir}/average/colortable_BA.txt ' \
              f'--l {hemi}.BA1_exvivo.thresh.label --l {hemi}.BA2_exvivo.thresh.label --l {hemi}.BA3a_exvivo.thresh.label ' \
              f'--l {hemi}.BA3b_exvivo.thresh.label --l {hemi}.BA4a_exvivo.thresh.label --l {hemi}.BA4p_exvivo.thresh.label ' \
              f'--l {hemi}.BA6_exvivo.thresh.label --l {hemi}.BA44_exvivo.thresh.label --l {hemi}.BA45_exvivo.thresh.label ' \
              f'--l {hemi}.V1_exvivo.thresh.label --l {hemi}.V2_exvivo.thresh.label --l {hemi}.MT_exvivo.thresh.label ' \
              f'--l {hemi}.perirhinal_exvivo.thresh.label --l {hemi}.entorhinal_exvivo.thresh.label --a BA_exvivo.thresh --maxstatwinner --noverbose'
        run_cmd_with_timing(cmd)
        cmd = f'mris_anatomical_stats -th3 -mgz -f {sub_stats_dir}/{hemi}.BA_exvivo.stats -b ' \
              f'-a {sub_label_dir}/{hemi}.BA_exvivo.annot ' \
              f'-c {sub_label_dir}/BA_exvivo.ctab {self.inputs.subject_id} {hemi} white'
        run_cmd_with_timing(cmd)
        cmd = f'mris_anatomical_stats -th3 -mgz -f {sub_stats_dir}/{hemi}.BA_exvivo.thresh.stats -b ' \
              f'-a {sub_label_dir}/{hemi}.BA_exvivo.thresh.annot ' \
              f'-c {sub_label_dir}/BA_exvivo.thresh.ctab {self.inputs.subject_id} {hemi} white'
        run_cmd_with_timing(cmd)

    def _run_interface(self, runtime):
        multipool(self.cmd, Multi_Num=2)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["lh_BA45_exvivo"] = self.inputs.lh_BA45_exvivo
        outputs["rh_BA45_exvivo"] = self.inputs.rh_BA45_exvivo
        outputs["lh_perirhinal_exvivo"] = self.inputs.lh_perirhinal_exvivo
        outputs["rh_perirhinal_exvivo"] = self.inputs.rh_perirhinal_exvivo
        outputs["BA_exvivo_thresh"] = self.inputs.BA_exvivo_thresh

        return outputs
