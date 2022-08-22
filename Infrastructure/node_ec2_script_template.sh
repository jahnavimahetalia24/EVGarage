sudo yum install python3-pip docker -y
sudo pip3 install docker-compose -y
sudo systemctl enable docker.service
sudo systemctl start docker.service
mkdir node
cd node
echo "FROM node:16.16.0
RUN apt update
RUN apt install net-tools lsof nano -y  # 
WORKDIR /home/node/
RUN git clone https://github.com/Defcon27/Autorizz-Car-Dealership-System-using-NodeJS-Express-MongoDB/ ev_garage
WORKDIR /home/node/ev_garage/
RUN sed -i 's/localhost/ec2_link/g' app.js
RUN npm install --quiet;" > Dockerfile 
sudo docker build -t ev_garage_node_image:node .;
sudo docker run -p 80:5000 -i ev_garage_node_image:node bash -c "npm install; npm start"
