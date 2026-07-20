###############################################################################
# SentinelAI - Dev Environment
# Smaller instances, cost-optimized for development
###############################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    bucket = "sentinelai-terraform-state"
    key    = "environments/dev/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "SentinelAI"
      Environment = "dev"
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  project_name = "sentinelai"
  environment  = "dev"
  region       = "us-east-1"
}

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------
module "vpc" {
  source = "../../modules/vpc"

  project_name        = local.project_name
  environment         = local.environment
  vpc_cidr            = "10.0.0.0/16"
  public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.20.0/24"]
  availability_zones  = ["us-east-1a", "us-east-1b"]
}

# -----------------------------------------------------------------------------
# ECS (smaller for dev)
# -----------------------------------------------------------------------------
module "ecs" {
  source = "../../modules/ecs"

  project_name          = local.project_name
  environment           = local.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  private_subnet_ids    = module.vpc.private_subnet_ids
  alb_security_group_id = module.vpc.alb_security_group_id
  ecs_security_group_id = module.vpc.ecs_security_group_id

  backend_cpu           = 256
  backend_memory        = 512
  frontend_cpu          = 256
  frontend_memory       = 512
  backend_desired_count = 1
  frontend_desired_count = 1
}

# -----------------------------------------------------------------------------
# RDS (smaller for dev)
# -----------------------------------------------------------------------------
module "rds" {
  source = "../../modules/rds"

  project_name             = local.project_name
  environment              = local.environment
  vpc_id                   = module.vpc.vpc_id
  private_subnet_ids       = module.vpc.private_subnet_ids
  rds_security_group_id    = module.vpc.rds_security_group_id

  db_instance_class        = "db.t3.small"
  db_allocated_storage     = 20
  db_max_allocated_storage = 50
  db_name                  = "sentinelai"
  db_username              = "sentinelai_dev"
  db_backup_retention_days = 3
  db_multi_az              = false
  enable_enhanced_monitoring = false
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "alb_dns_name" {
  value = module.ecs.alb_dns_name
}

output "ecr_backend_url" {
  value = module.ecs.ecr_backend_url
}

output "ecr_frontend_url" {
  value = module.ecs.ecr_frontend_url
}

output "rds_endpoint" {
  value     = module.rds.endpoint
  sensitive = true
}
