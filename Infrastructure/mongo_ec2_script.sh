sudo yum install python3-pip docker -y
sudo pip3 install docker-compose -y
sudo systemctl enable docker.service
sudo systemctl start docker.service
mkdir mongodb
cd mongodb/
echo "FROM mongo:latest
RUN apt update
RUN apt install git systemctl net-tools lsof nano -y
WORKDIR /
RUN git clone https://github.com/Defcon27/Autorizz-Car-Dealership-System-using-NodeJS-Express-MongoDB/ ev_garage
WORKDIR /ev_garage/db_data" > Dockerfile
sudo docker build -t ev_garage_mongodb_image:mongodb .;
sudo docker run -p 27017:27017 -i ev_garage_mongodb_image:mongodb bash -c 'bash -c "ifconfig|grep inet; mongod --port 27017 --bind_ip_all --fork --logpath mongodb.log; mongoimport -d autorizz --jsonArray  --file customer.json; mongoimport -d autorizz --jsonArray  --file electricmodel.json; mongoimport -d autorizz --jsonArray  --file gasmodel.json; mongoimport -d autorizz --jsonArray  --file service.json; mongoimport -d autorizz --jsonArray  --file user.json; lsof -iTCP -sTCP:LISTEN | grep mongo;while 1>0; do sleep 1000; done"'
