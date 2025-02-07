
# ssh gcp-us-storage sudo systemctl start insait-dataset-sync.service

DPATH=$1
NAME=$(basename $DPATH)
# rsync -aP $(rsync-path $DATASET_DPATH) /scratch/nedko_savov/projects/ivg/datasets/
mkdir -p $DPATH
unsquashfs -d $DPATH /work/datasets/$NAME.squashfs