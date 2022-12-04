kubectl apply -f frontend/frontend-deployment.yaml
kubectl apply -f frontend/frontend-ingress.yaml
kubectl apply -f frontend/frontend-service.yaml

kubectl apply -f recognition-service/recognition-deployment.yaml

kubectl apply -f segmenting-service/segmentation-deployment.yaml

kubectl apply -f redis/redis-deployment.yaml
kubectl apply -f redis/redis-service.yaml