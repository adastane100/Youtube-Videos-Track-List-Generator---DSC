kubectl apply -f frontend/frontend-deployment.yaml
kubectl apply -f frontend/frontend-ingress.yaml
kubectl apply -f frontend/frontend-service.yaml

kubectl apply -f downloading-service/downloading-deployment.yaml
kubectl apply -f recognition-service/recognition-deployment.yaml
kubectl apply -f segmenting-service/segmentation-deployment.yaml
kubectl apply -f uniqueness-service/uniqueness-deployment.yaml

kubectl apply -f redis/redis-deployment.yaml
kubectl apply -f redis/redis-service.yaml

kubectl apply -f minio/minio-external-service.yaml

kubectl apply -f logs/logs-deployment.yaml

# kubectl port-forward --namespace minio-ns svc/minio-proj 9001:9001
# kubectl port-forward service/redis 6379:6379