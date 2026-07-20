###############################################################################
# SentinelAI - Production Environment
# Multi-AZ, larger instances, enhanced monitoring, deletion protection
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
    bucket         = "sentinelai-terraform-state"
    key            = "environments/prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "sentinelai-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "SentinelAI"
      Environment = "prod"
      ManagedBy   = "Terraform"
      CostCenter  = "engineering"
    }
  }
}

locals {
  project_name = "sentinelai"
  environment  = "prod"
  region       = "us-east-1"
}

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------
module "vpc" {
  source = "../../modules/vpc"

  project_name         = local.project_name
  environment          = local.environment
  vpc_cidr             = "10.1.0.0/16"
  public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
  private_subnet_cidrs = ["10.1.10.0/24", "10.1.20.0/24"]
  availability_zones   = ["us-east-1a", "us-east-1b"]
}

# -----------------------------------------------------------------------------
# ECS (production-grade)
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

  backend_cpu            = 1024
  backend_memory         = 2048
  frontend_cpu           = 512
  frontend_memory        = 1024
  backend_desired_count  = 3
  frontend_desired_count = 2

  certificate_arn = var.certificate_arn
}

# -----------------------------------------------------------------------------
# RDS (production-grade)
# -----------------------------------------------------------------------------
module "rds" {
  source = "../../modules/rds"

  project_name             = local.project_name
  environment              = local.environment
  vpc_id                   = module.vpc.vpc_id
  private_subnet_ids       = module.vpc.private_subnet_ids
  rds_security_group_id    = module.vpc.rds_security_group_id

  db_instance_class          = "db.t3.medium"
  db_allocated_storage       = 50
  db_max_allocated_storage   = 200
  db_name                    = "sentinelai"
  db_username                = "sentinelai_admin"
  db_backup_retention_days   = 7
  db_multi_az                = true
  enable_enhanced_monitoring = true
}

# -----------------------------------------------------------------------------
# Variables
# -----------------------------------------------------------------------------
variable "certificate_arn" {
  description = "ARN of ACM certificate for HTTPS"
  type        = string
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "alb_dns_name" {
  description = "Production ALB DNS name"
  value       = module.ecs.alb_dns_name
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

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "backend_service_name" {
  value = module.ecs.backend_service_name
}

output "frontend_service_name" {
  value = module.ecs.frontend_service_name
}
