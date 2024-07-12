docker build -t maes95/outsider-backend:1.0.0 .
docker push maes95/outsider-backend:1.0.1
docker build -t maes95/outsider-front:1.0.1 -f outsider-front/Dockerfile outsider-front/
docker push maes95/outsider-front:1.0.1