# SentinelAI - Terraform Infrastructure
# Main configuration for AWS deployment

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "sentinelai-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SentinelAI"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ==============================================================================
# Local Values
# ==============================================================================

locals {
  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
  })
}

# ==============================================================================
# VPC Module
# ==============================================================================

module "vpc" {
  source = "./modules/vpc"

  project_name         = var.project_name
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
  tags                 = local.common_tags
}

# ==============================================================================
# RDS Module
# ==============================================================================

module "rds" {
  source = "./modules/rds"

  project_name               = var.project_name
  environment                = var.environment
  vpc_id                     = module.vpc.vpc_id
  private_subnet_ids         = module.vpc.private_subnet_ids
  db_instance_class          = var.db_instance_class
  db_allocated_storage       = var.db_allocated_storage
  db_max_allocated_storage   = var.db_max_allocated_storage
  db_name                    = var.db_name
  db_username                = var.db_username
  db_password                = var.db_password
  multi_az                   = var.db_multi_az
  backup_retention_period    = var.db_backup_retention_period
  allowed_security_group_ids = [module.ecs.ecs_tasks_security_group_id]
  tags                       = local.common_tags
}

# ==============================================================================
# ECS Module
# ==============================================================================

module "ecs" {
  source = "./modules/ecs"

  project_name                = var.project_name
  environment                 = var.environment
  vpc_id                      = module.vpc.vpc_id
  public_subnet_ids           = module.vpc.public_subnet_ids
  private_subnet_ids          = module.vpc.private_subnet_ids
  backend_image               = var.backend_image
  frontend_image              = var.frontend_image
  backend_cpu                 = var.backend_cpu
  backend_memory              = var.backend_memory
  frontend_cpu                = var.frontend_cpu
  frontend_memory             = var.frontend_memory
  backend_desired_count       = var.backend_desired_count
  frontend_desired_count      = var.frontend_desired_count
  backend_min_count           = var.backend_min_count
  backend_max_count           = var.backend_max_count
  backend_auto_scaling_target = var.backend_auto_scaling_target
  certificate_arn             = var.certificate_arn
  tags                        = local.common_tags

  backend_environment = [
    { name = "APP_ENV", value = var.environment },
    { name = "DATABASE_URL", value = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${module.rds.endpoint}/${var.db_name}" },
    { name = "REDIS_URL", value = "redis://redis:6379/0" },
    { name = "OLLAMA_HOST", value = "http://ollama:11434" },
    { name = "CORS_ORIGINS", value = var.domain_name != "" ? "https://${var.domain_name}" : "*" },
  ]
}
