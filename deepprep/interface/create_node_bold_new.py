from interface.bold_node_new import *
from interface.vxm_node import *
from interface.node_source import Source

from nipype import Node

"""环境变量
subjects_dir = Path(os.environ['SUBJECTS_DIR'])
bold_preprocess_dir = Path(os.environ['BOLD_PREPROCESS_DIR'])
workflow_cached_dir = Path(os.environ['WORKFLOW_CACHED_DIR'])
fastsurfer_home = Path(os.environ['FASTSURFER_HOME'])
freesurfer_home = Path(os.environ['FREESURFER_HOME'])
fastcsr_home = Path(os.environ['FASTCSR_HOME'])
featreg_home = Path(os.environ['FEATREG_HOME'])
python_interpret = sys.executable
"""


def create_VxmRegistraion_node(subject_id: str, task: str, atlas_type: str, preprocess_method: str):
    subjects_dir = Path(os.environ['SUBJECTS_DIR'])
    derivative_deepprep_path = os.environ['BOLD_PREPROCESS_DIR']
    workflow_cached_dir = Path(os.environ['WORKFLOW_CACHED_DIR'])
    data_path = Path(os.environ['BIDS_DIR'])
    vxm_model_path = Path(os.environ['VXM_MODEL_PATH'])
    gpuid = os.environ['DEEPPREP_DEVICES']

    VxmRegistraion_node = Node(VxmRegistraion(), name=f'{subject_id}_bold_VxmRegistraion_node')
    VxmRegistraion_node.inputs.subject_id = subject_id
    VxmRegistraion_node.inputs.data_path = data_path
    VxmRegistraion_node.inputs.derivative_deepprep_path = derivative_deepprep_path
    VxmRegistraion_node.inputs.subjects_dir = subjects_dir
    VxmRegistraion_node.inputs.model_file = vxm_model_path / atlas_type / 'model.h5'
    VxmRegistraion_node.inputs.vxm_model_path = vxm_model_path
    VxmRegistraion_node.inputs.atlas_type = atlas_type
    VxmRegistraion_node.inputs.task = task
    VxmRegistraion_node.inputs.preprocess_method = preprocess_method
    VxmRegistraion_node.inputs.gpuid = gpuid

    VxmRegistraion_node.base_dir = workflow_cached_dir
    VxmRegistraion_node.source = Source(CPU_n=1, GPU_MB=2715, RAM_MB=3000, IO_write_MB=0, IO_read_MB=0)

    VxmRegistraion_node.interface.bold_only = os.environ['BOLD_ONLY']

    return VxmRegistraion_node


def create_BoldSkipReorient_node(subject_id: str, task: str, atlas_type: str, preprocess_method: str):
    workflow_cached_dir = Path(os.environ['WORKFLOW_CACHED_DIR'])
    derivative_deepprep_path = Path(os.environ['BOLD_PREPROCESS_DIR'])
    data_path = Path(os.environ['BIDS_DIR'])

    BoldSkipReorient_node = Node(BoldSkipReorient(), name=f'{subject_id}_bold_BoldSkipReorient_node')
    BoldSkipReorient_node.inputs.subject_id = subject_id
    BoldSkipReorient_node.inputs.data_path = data_path
    BoldSkipReorient_node.inputs.derivative_deepprep_path = derivative_deepprep_path
    BoldSkipReorient_node.inputs.task = task
    BoldSkipReorient_node.inputs.atlas_type = atlas_type
    BoldSkipReorient_node.inputs.preprocess_method = preprocess_method
    BoldSkipReorient_node.inputs.nskip_frame = "0"
    BoldSkipReorient_node.inputs.multiprocess = "1"

    BoldSkipReorient_node.base_dir = workflow_cached_dir
    BoldSkipReorient_node.source = Source(CPU_n=0, GPU_MB=0, RAM_MB=1000, IO_write_MB=20, IO_read_MB=40)

    BoldSkipReorient_node.interface.bold_only = os.environ['BOLD_ONLY']

    return BoldSkipReorient_node


def create_StcMc_node(subject_id: str, task: str, atlas_type: str, preprocess_method: str):
    workflow_cached_dir = Path(os.environ['WORKFLOW_CACHED_DIR'])
    derivative_deepprep_path = Path(os.environ['BOLD_PREPROCESS_DIR'])
    data_path = Path(os.environ['BIDS_DIR'])

    StcMc_node = Node(StcMc(), name=f'{subject_id}_bold_StcMc_node')
    StcMc_node.inputs.subject_id = subject_id
    StcMc_node.inputs.task = task
    StcMc_node.inputs.data_path = data_path
    StcMc_node.inputs.derivative_deepprep_path = derivative_deepprep_path
    StcMc_node.inputs.atlas_type = atlas_type
    StcMc_node.inputs.preprocess_method = preprocess_method
    StcMc_node.inputs.multiprocess = "1"

    StcMc_node.base_dir = workflow_cached_dir
    StcMc_node.source = Source(CPU_n=0, GPU_MB=0, RAM_MB=1000, IO_write_MB=20, IO_read_MB=40)

    StcMc_node.interface.bold_only = os.environ['BOLD_ONLY']

    return StcMc_node


def create_Register_node(subject_id: str, task: str, atlas_type: str, preprocess_method: str):
    workflow_cached_dir = Path(os.environ['WORKFLOW_CACHED_DIR'])
    derivative_deepprep_path = Path(os.environ['BOLD_PREPROCESS_DIR'])
    data_path = Path(os.environ['BIDS_DIR'])

    Register_node = Node(Register(), name=f'{subject_id}_bold_Register_node')
    Register_node.inputs.subject_id = subject_id
    Register_node.inputs.task = task
    Register_node.inputs.data_path = data_path
    Register_node.inputs.derivative_deepprep_path = derivative_deepprep_path
    Register_node.inputs.atlas_type = atlas_type
    Register_node.inputs.preprocess_method = preprocess_method
    Register_node.inputs.multiprocess = "1"

    Register_node.base_dir = workflow_cached_dir
    Register_node.source = Source(CPU_n=0, GPU_MB=0, RAM_MB=1000, IO_write_MB=20, IO_read_MB=40)

    Register_node.interface.bold_only = os.environ['BOLD_ONLY']

    return Register_node


def create_Mkbrainmask_node(subject_id: str, task: str, atlas_type: str, preprocess_method: str):
    workflow_cached_dir = Path(os.environ['WORKFLOW_CACHED_DIR'])
    derivative_deepprep_path = Path(os.environ['BOLD_PREPROCESS_DIR'])
    data_path = Path(os.environ['BIDS_DIR'])
    subjects_dir = Path(os.environ['SUBJECTS_DIR'])

    Mkbrainmask_node = Node(MkBrainmask(), name=f'{subject_id}_bold_MkBrainmask_node')
    Mkbrainmask_node.inputs.subject_id = subject_id
    Mkbrainmask_node.inputs.subjects_dir = subjects_dir
    Mkbrainmask_node.inputs.task = task
    Mkbrainmask_node.inputs.data_path = data_path
    Mkbrainmask_node.inputs.derivative_deepprep_path = derivative_deepprep_path
    Mkbrainmask_node.inputs.atlas_type = atlas_type
    Mkbrainmask_node.inputs.preprocess_method = preprocess_method
    Mkbrainmask_node.inputs.multiprocess = "1"

    Mkbrainmask_node.base_dir = workflow_cached_dir
    Mkbrainmask_node.source = Source(CPU_n=0, GPU_MB=0, RAM_MB=1000, IO_write_MB=20, IO_read_MB=40)

    Mkbrainmask_node.interface.bold_only = os.environ['BOLD_ONLY']

    return Mkbrainmask_node


def create_RestGauss_node(subject_id: str, task: str, atlas_type: str, preprocess_method: str):
    workflow_cached_dir = Path(os.environ['WORKFLOW_CACHED_DIR'])
    derivative_deepprep_path = Path(os.environ['BOLD_PREPROCESS_DIR'])
    data_path = Path(os.environ['BIDS_DIR'])
    subjects_dir = Path(os.environ['SUBJECTS_DIR'])

    RestGauss_node = Node(RestGauss(), name=f'{subject_id}_bold_RestGauss_node')
    RestGauss_node.inputs.subject_id = subject_id
    RestGauss_node.inputs.subjects_dir = subjects_dir
    RestGauss_node.inputs.data_path = data_path
    RestGauss_node.inputs.task = task
    RestGauss_node.inputs.derivative_deepprep_path = derivative_deepprep_path
    RestGauss_node.inputs.atlas_type = atlas_type
    RestGauss_node.inputs.preprocess_method = preprocess_method

    RestGauss_node.base_dir = workflow_cached_dir
    RestGauss_node.source = Source(CPU_n=0, GPU_MB=0, RAM_MB=2000, IO_write_MB=0, IO_read_MB=0)

    RestGauss_node.interface.bold_only = os.environ['BOLD_ONLY']

    return RestGauss_node


def create_RestBandpass_node(subject_id: str, task: str, atlas_type: str, preprocess_method: str):
    workflow_cached_dir = Path(os.environ['WORKFLOW_CACHED_DIR'])
    derivative_deepprep_path = Path(os.environ['BOLD_PREPROCESS_DIR'])
    data_path = Path(os.environ['BIDS_DIR'])

    RestBandpass_node = Node(RestBandpass(), name=f'{subject_id}_bold_RestBandpass_node')
    RestBandpass_node.inputs.subject_id = subject_id
    RestBandpass_node.inputs.data_path = data_path
    RestBandpass_node.inputs.task = task
    RestBandpass_node.inputs.derivative_deepprep_path = derivative_deepprep_path
    RestBandpass_node.inputs.atlas_type = atlas_type
    RestBandpass_node.inputs.preprocess_method = preprocess_method

    RestBandpass_node.base_dir = workflow_cached_dir
    RestBandpass_node.source = Source(CPU_n=0, GPU_MB=0, RAM_MB=3000, IO_write_MB=0, IO_read_MB=0)

    RestBandpass_node.interface.bold_only = os.environ['BOLD_ONLY']

    return RestBandpass_node


def create_RestRegression_node(subject_id: str, task: str, atlas_type: str, preprocess_method: str):
    workflow_cached_dir = Path(os.environ['WORKFLOW_CACHED_DIR'])
    derivative_deepprep_path = Path(os.environ['BOLD_PREPROCESS_DIR'])
    data_path = Path(os.environ['BIDS_DIR'])
    subjects_dir = Path(os.environ['SUBJECTS_DIR'])

    RestRegression_node = Node(RestRegression(), name=f'{subject_id}_bold_RestRegression_node')
    RestRegression_node.inputs.subject_id = subject_id
    RestRegression_node.inputs.subjects_dir = subjects_dir
    RestRegression_node.inputs.data_path = data_path
    RestRegression_node.inputs.task = task
    RestRegression_node.inputs.derivative_deepprep_path = derivative_deepprep_path
    RestRegression_node.inputs.atlas_type = atlas_type
    RestRegression_node.inputs.preprocess_method = preprocess_method

    RestRegression_node.base_dir = workflow_cached_dir
    RestRegression_node.source = Source(CPU_n=0, GPU_MB=0, RAM_MB=4000, IO_write_MB=20, IO_read_MB=40)

    RestRegression_node.interface.bold_only = os.environ['BOLD_ONLY']

    return RestRegression_node


def create_VxmRegNormMNI152_node(subject_id: str, task: str, atlas_type: str, preprocess_method: str):
    workflow_cached_dir = Path(os.environ['WORKFLOW_CACHED_DIR'])
    derivative_deepprep_path = Path(os.environ['BOLD_PREPROCESS_DIR'])
    data_path = Path(os.environ['BIDS_DIR'])
    subjects_dir = Path(os.environ['SUBJECTS_DIR'])
    vxm_model_path = Path(os.environ['VXM_MODEL_PATH'])
    resource_dir = Path(os.environ['RESOURCE_DIR'])
    gpuid = os.environ['DEEPPREP_DEVICES']

    VxmRegNormMNI152_node = Node(VxmRegNormMNI152(), name=f'{subject_id}_bold_VxmRegNormMNI152_node')
    VxmRegNormMNI152_node.inputs.subjects_dir = subjects_dir
    VxmRegNormMNI152_node.inputs.subject_id = subject_id
    VxmRegNormMNI152_node.inputs.atlas_type = atlas_type
    VxmRegNormMNI152_node.inputs.task = task
    VxmRegNormMNI152_node.inputs.data_path = data_path
    VxmRegNormMNI152_node.inputs.preprocess_method = preprocess_method
    VxmRegNormMNI152_node.inputs.vxm_model_path = vxm_model_path
    VxmRegNormMNI152_node.inputs.resource_dir = resource_dir
    VxmRegNormMNI152_node.inputs.derivative_deepprep_path = derivative_deepprep_path
    VxmRegNormMNI152_node.inputs.gpuid = gpuid

    VxmRegNormMNI152_node.base_dir = workflow_cached_dir
    VxmRegNormMNI152_node.source = Source(CPU_n=0, GPU_MB=4529, RAM_MB=15000, IO_write_MB=0, IO_read_MB=0)

    VxmRegNormMNI152_node.interface.bold_only = os.environ['BOLD_ONLY']

    return VxmRegNormMNI152_node


def create_Smooth_node(subject_id: str, task: str, atlas_type: str, preprocess_method: str):
    workflow_cached_dir = Path(os.environ['WORKFLOW_CACHED_DIR'])
    derivative_deepprep_path = Path(os.environ['BOLD_PREPROCESS_DIR'])
    data_path = Path(os.environ['BIDS_DIR'])
    mni152_brain_mask = Path(os.environ['MNI152_BRAIN_MASK'])

    Smooth_node = Node(Smooth(), name=f'{subject_id}_Smooth_node')
    Smooth_node.inputs.subject_id = subject_id
    Smooth_node.inputs.task = task
    Smooth_node.inputs.data_path = data_path
    Smooth_node.inputs.atlas_type = atlas_type
    Smooth_node.inputs.preprocess_method = preprocess_method
    Smooth_node.inputs.MNI152_T1_2mm_brain_mask = mni152_brain_mask
    Smooth_node.inputs.derivative_deepprep_path = derivative_deepprep_path

    Smooth_node.base_dir = workflow_cached_dir
    Smooth_node.source = Source(CPU_n=0, GPU_MB=0, RAM_MB=7500, IO_write_MB=0, IO_read_MB=0)

    Smooth_node.interface.bold_only = os.environ['BOLD_ONLY']

    return Smooth_node


def create_node_t():
    from interface.run import set_envrion
    set_envrion(threads=8)

    pwd = Path.cwd()
    pwd = pwd.parent
    fastsurfer_home = pwd / "FastSurfer"
    freesurfer_home = Path('/usr/local/freesurfer720')
    fastcsr_home = pwd / "FastCSR"
    featreg_home = pwd / "FeatReg"

    bids_data_dir_test = '/mnt/ngshare/temp/UKB'
    subjects_dir_test = Path('/mnt/ngshare/temp/UKB_Recon')
    bold_preprocess_dir_test = Path('/mnt/ngshare/temp/UKB_BoldPreprocess')
    workflow_cached_dir_test = '/mnt/ngshare/temp/UKB_Workflow'
    vxm_model_path_test = '../model/voxelmorph'
    mni152_brain_mask_test = '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain_mask.nii.gz'
    resource_dir_test = '../resource'

    if not subjects_dir_test.exists():
        subjects_dir_test.mkdir(parents=True, exist_ok=True)

    if not bold_preprocess_dir_test.exists():
        bold_preprocess_dir_test.mkdir(parents=True, exist_ok=True)

    subject_id_test = 'sub-1000525'

    # t1w_files = ['/mnt/ngshare/DeepPrep_workflow_test/UKB_BIDS/sub-1000037/ses-02/anat/sub-1000037_ses-02_T1w.nii.gz']

    os.environ['SUBJECTS_DIR'] = str(subjects_dir_test)
    os.environ['BOLD_PREPROCESS_DIR'] = str(bold_preprocess_dir_test)
    os.environ['WORKFLOW_CACHED_DIR'] = str(workflow_cached_dir_test)
    os.environ['FASTSURFER_HOME'] = str(fastsurfer_home)
    os.environ['FREESURFER_HOME'] = str(freesurfer_home)
    os.environ['FASTCSR_HOME'] = str(fastcsr_home)
    os.environ['FEATREG_HOME'] = str(featreg_home)
    os.environ['BIDS_DIR'] = bids_data_dir_test
    os.environ['VXM_MODEL_PATH'] = str(vxm_model_path_test)
    os.environ['MNI152_BRAIN_MASK'] = str(mni152_brain_mask_test)
    os.environ['RESOURCE_DIR'] = str(resource_dir_test)
    os.environ['DEEPPREP_DEVICES'] = 'cuda'

    atlas_type_test = 'MNI152_T1_2mm'
    task_test = 'rest'
    preprocess_method_test = 'task'

    os.environ['DEEPPREP_ATLAS_TYPE'] = atlas_type_test
    os.environ['DEEPPREP_TASK'] = task_test
    os.environ['DEEPPREP_PREPROCESS_METHOD'] = preprocess_method_test

    os.environ['RECON_ONLY'] = 'False'
    os.environ['BOLD_ONLY'] = 'False'

    print('#####################################################1#####################################################')

    node = create_BoldSkipReorient_node(subject_id=subject_id_test, task=task_test, atlas_type=atlas_type_test,
                                        preprocess_method=preprocess_method_test)
    node.run()
    # sub_node = node.interface.create_sub_node()
    # sub_node.run()

    print('#####################################################2#####################################################')
    node = create_StcMc_node(subject_id=subject_id_test, task=task_test, atlas_type=atlas_type_test,
                             preprocess_method=preprocess_method_test)
    node.run()
    # sub_node = node.interface.create_sub_node()
    # sub_node.run()

    print('#####################################################3#####################################################')
    node = create_Register_node(subject_id=subject_id_test, task=task_test, atlas_type=atlas_type_test,
                                preprocess_method=preprocess_method_test)
    node.run()
    # sub_node = node.interface.create_sub_node()
    # sub_node.run()

    print('#####################################################4#####################################################')
    node = create_Mkbrainmask_node(subject_id=subject_id_test, task=task_test, atlas_type=atlas_type_test,
                                   preprocess_method=preprocess_method_test)
    node.run()
    # sub_node = node.interface.create_sub_node()
    # sub_node.run()
    return
    print('#####################################################5#####################################################')
    node = create_VxmRegistraion_node(subject_id=subject_id_test, task=task_test, atlas_type=atlas_type_test,
                             preprocess_method=preprocess_method_test)
    node.run()
    # sub_node = node.interface.create_sub_node()
    # sub_node.run()
    print('####################################################6####################################################')
    node = create_VxmRegNormMNI152_node(subject_id=subject_id_test, task=task_test, atlas_type=atlas_type_test,
                                        preprocess_method=preprocess_method_test)
    node.run()
    # sub_node = node.interface.create_sub_node()
    # sub_node.run()
    exit()
    print('#####################################################7#####################################################')
    node = create_RestGauss_node(subject_id=subject_id_test, task=task_test, atlas_type=atlas_type_test,
                                 preprocess_method=preprocess_method_test)
    node.run()
    # sub_node = node.interface.create_sub_node()
    # sub_node.run()
    print('#####################################################8#####################################################')
    node = create_RestBandpass_node(subject_id=subject_id_test, task=task_test, atlas_type=atlas_type_test,
                                    preprocess_method=preprocess_method_test)
    node.run()
    # sub_node = node.interface.create_sub_node()
    # sub_node.run()
    print('#####################################################6#####################################################')

    node = create_RestRegression_node(subject_id=subject_id_test, task=task_test, atlas_type=atlas_type_test,
                                      preprocess_method=preprocess_method_test)
    node.run()
    # sub_node = node.interface.create_sub_node()
    # sub_node.run()
    print('####################################################11####################################################')
    node = create_Smooth_node(subject_id=subject_id_test, task=task_test, atlas_type=atlas_type_test,
                              preprocess_method=preprocess_method_test)
    node.run()


if __name__ == '__main__':
    create_node_t()  # 测试