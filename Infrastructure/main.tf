provider "aws" {
  region = "us-east-1"
  alias = "east"
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
  instance_type               = "t2.micro"
  user_data                   = <<EOF
  #!/bin/bash
  sudo apt-get install docker-engine -y
  sudo service docker start
  sudo docker run hello-world
  EOF
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