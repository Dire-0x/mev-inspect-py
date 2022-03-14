#!/bin/bash

IMAGE_NAME=mev-inspect-py

# build the image
docker buildx build --platform linux/amd64 -t $IMAGE_NAME:latest --load .

# login to docker w/ erc credentials
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# tag the image as latest
now=$(date '+%s')

docker tag $IMAGE_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$now
docker tag $IMAGE_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:latest

# push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:latest | sed "s/$AWS_ACCOUNT_ID/<AWS_ACCOUNT_ID>/"
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$now | sed "s/$AWS_ACCOUNT_ID/<AWS_ACCOUNT_ID>/"

# update the helm deployments
helm upgrade mev-inspect k8s/mev-inspect --set=image.repository=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$now
helm upgrade mev-inspect-prices k8s/mev-inspect-prices --set=image.repository=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$now
helm upgrade mev-inspect-workers k8s/mev-inspect-workers --set=image.repository=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$now --set=replicaCount=24

#  first deployment
# helm repo add bitnami https://charts.bitnami.com/bitnami
# helm install redis bitnami/redis --set=global.redis.password=$REDIS_PASSWORD
# helm install mev-inspect k8s/mev-inspect --set=image.repository=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$now
# helm install mev-inspect-prices k8s/mev-inspect-prices --set=image.repository=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$now
# helm install mev-inspect-workers k8s/mev-inspect-workers --set=image.repository=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$now --set=replicaCount=24
