provider "aws" {
  region = "us-east-1"
  alias = "east"
}

resource "aws_key_pair" "name" {
  key_name = "deployer_key"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQD0W0lZwALc8CkBSebs9Pf6NdpgT+4hk3/JeIzQyzX0dJoTajTcko8Lr2+/3ctngGNUeryrLawP4NRdT8WaxjWej6cHPvuz14fIuYHoJpWel2C+GILLQstzHLLnpon8D7JmXDdlGzcT9L9QQaJ3kQLsu4SZkuNsUX+CZ4kxIA34yVVpHM/StMrSQBAtciGdCBLUh/Wv3NMomFZS+YjMWH5/uiJbtRy17XO1Z0d7pZbnj6bWL/azXUmyj9jUPV7EhQUVoUM54sy8H22YrHHUGiymbbjSwozU5RTGEibqFSW6G+RVWvDSKXsSFrNWeGLwSVBjFnMLbLvxLdYPhIPCipTlB+0uQyKIEx8nbWSnXh1pQwQApMPYngVhco8Yj7nlJ/Uk9K8c/cAwGT5C5kiQXMEQNgZwUbAOH8d2lB5QO5zXq/fva+Osinm5AZ5/CEYKhlZ91hFLkXT2ePzbCxSdK3s9d0VGcUQKoCHWAbXaDifLaOrWHaDU2zx77fNiz3k/i28= jahnavimahetalia@Jahnavis-MacBook-Air.local"
}

data "aws_ami" "i" {
  provider = aws.east
  owners = ["amazon"]
  most_recent = true

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-ebs"]
  }
}

resource "aws_launch_configuration" "webserver" {
  name_prefix                 = "jahnavi"
  image_id                    = data.aws_ami.i.id
  key_name                    = "deployer_key"
  #ami                        = "ami-052efd3df9dad4825"
  instance_type               = "t2.micro"
  security_groups = [
    aws_security_group.default.id
  ]
  depends_on = [
    aws_internet_gateway.default
  ]
  #user_data                  = 
  associate_public_ip_address = true
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "webserver" {
  #availability_zones   = ["us-east-1a", "us-east-1b"]
  name                 = "autoscalinggroupfinalproject"
  launch_configuration = aws_launch_configuration.webserver.name
  min_size             = 2
  max_size             = 3
  desired_capacity     = 2
  vpc_zone_identifier = [
    aws_subnet.public__a.id,
    aws_subnet.public__b.id
  ]
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "database" {
  #availability_zones   = ["us-east-1a", "us-east-1b"]
  name                 = "autoscalinggroup2"
  launch_configuration = aws_launch_configuration.webserver.name
  min_size             = 2
  max_size             = 3
  desired_capacity     = 2
  vpc_zone_identifier = [
    aws_subnet.public__a.id,
    aws_subnet.public__b.id
  ]
  lifecycle {
    create_before_destroy = true
  }
}