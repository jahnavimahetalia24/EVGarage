provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  region = "us-east-1"
  alias = "east"
}

resource "aws_key_pair" "name" {
  key_name = "deployer_key"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDK2ZzY3Tmx/8FjkB2dtn9EBH/pk1I7VkPfZR+O8w33mWfyjLEjqmitWQJ3e6Cn6pH2tCbhLIH9lyLkSWKVUDeWNu5Fw0SvjJp0M1nQ+4CUHRmuejtZyj4sYg2ymmmXNSFUb0ywotdfzJUUcRme6GEB9nylbBuLHKGVjovB5eEw/+dfnh9DymqxcHY5zTdjHYuKZdhJBrHUyboidElb0mlV2sGc1ROGZ+NE+DRbMyXOSh+eWn2yz2iVzoDA/IpqcAe04ExADi6EYTKmK+NycmmNjYroj0T2P1QzlpcSE7+OsZj5w1aIsEfLjYFR2nYfc4jKCXl80fcFvNNQbRMf3EZF kalyanpatnaik96@gmail.com"
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

