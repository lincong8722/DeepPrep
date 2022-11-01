import os
from pathlib import Path


def rsync(o_dir, d_dir, user=None, host=None):
    if user is not None and host is not None:
        cmd = f'rsync --remove-source-files -rav {o_dir}/ {user}@{host}:{d_dir}'
    else:
        cmd = f'rsync -rav {o_dir}/ {d_dir}'
    os.system(cmd)


def main():
    # user = 'pbfs20'
    # host = '30.30.30.73'

    user = None
    host = None

    src_bold_dir = Path('/mnt/ngshare2/DeepPrep_UKB_500/UKB_BoldPreprocess')
    src_recon_dir = Path('/mnt/ngshare2/DeepPrep_UKB/UKB_Recon')
    dst_bold_dir = Path('/mnt/ngshare2/DeepPrep_UKB_500/UKB_BoldPreprocess')
    dst_recon_dir = Path('/mnt/ngshare2/DeepPrep_UKB/UKB_Recon')

    subject_filter_file = Path('/mnt/ngshare2/UKB/allsub_keep_3747_fieldid_1500_first_complete_1500.csv')

    with open(subject_filter_file, 'r') as f:
        subject_filter_ids = f.readlines()
        subject_filter_ids = [i.strip() for i in subject_filter_ids]
        subject_filter_ids = [i.replace('sub-', '') for i in subject_filter_ids]
        subject_filter_ids = set(subject_filter_ids)

    for subject_id in os.listdir(src_bold_dir):
        if subject_filter_ids is not None and subject_id.split('-')[1] not in subject_filter_ids:
            continue
        else:
            print(subject_id)
            src_dir = src_bold_dir / subject_id
            dst_dir = dst_bold_dir / subject_id
            rsync(src_dir, dst_dir, user, host)

    for subject_id in os.listdir(src_recon_dir):
        if subject_id not in subject_filter_ids:
            continue
        elif 'fsaverage' in subject_id:
            continue
        else:
            src_dir = src_recon_dir / subject_id
            dst_dir = dst_recon_dir / subject_id
            rsync(src_dir, dst_dir, user, host)


if __name__ == '__main__':
    # src_bold_dir = Path('/mnt/ngshare/DeepPrep_UKB_500/UKB_BoldPreprocess')
    # dst_bold_dir = Path('/mnt/ngshare2/DeepPrep_UKB_500/UKB_BoldPreprocess')
    # rsync(src_bold_dir, dst_bold_dir)
    main()
