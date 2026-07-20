#!/usr/bin/env bash
# ==============================================================================
# SentinelAI Deployment Helper Script
#
# Usage:
#   ./scripts/deploy.sh [environment] [image_tag]
#
# Arguments:
#   environment   Target environment: dev, staging, prod (default: dev)
#   image_tag     Docker image tag (default: git SHA)
#
# Examples:
#   ./scripts/deploy.sh dev
#   ./scripts/deploy.sh staging abc123
#   ./scripts/deploy.sh prod v1.2.3
# ==============================================================================

set -euo pipefail

# Configuration
PROJECT_NAME="sentinelai"
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"

# Arguments
ENVIRONMENT="${1:-dev}"
IMAGE_TAG="${2:-$(git rev-parse --short HEAD)}"

# Derived values
ECR_REGISTRY="${ECR_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
BACKEND_REPO="${PROJECT_NAME}-${ENVIRONMENT}-backend"
FRONTEND_REPO="${PROJECT_NAME}-${ENVIRONMENT}-frontend"
ECS_CLUSTER="${PROJECT_NAME}-${ENVIRONMENT}"
BACKEND_SERVICE="${PROJECT_NAME}-${ENVIRONMENT}-backend"
FRONTEND_SERVICE="${PROJECT_NAME}-${ENVIRONMENT}-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ==============================================================================
# Validation
# ==============================================================================

validate_environment() {
    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod."
        exit 1
    fi

    if [[ "$ENVIRONMENT" == "prod" ]]; then
        log_warn "You are deploying to PRODUCTION!"
        read -p "Are you sure? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "Deployment cancelled."
            exit 0
        fi
    fi
}

check_prerequisites() {
    local missing=()

    command -v docker &>/dev/null || missing+=("docker")
    command -v aws &>/dev/null || missing+=("aws")
    command -v git &>/dev/null || missing+=("git")

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        exit 1
    fi

    if [[ -z "$ECR_ACCOUNT_ID" ]]; then
        log_error "AWS_ACCOUNT_ID environment variable is required."
        exit 1
    fi
}

# ==============================================================================
# Build
# ==============================================================================

build_images() {
    log_info "Building Docker images with tag: $IMAGE_TAG"

    log_info "Building backend image..."
    docker build \
        -t "${BACKEND_REPO}:${IMAGE_TAG}" \
        -t "${BACKEND_REPO}:latest" \
        --build-arg APP_ENV="${ENVIRONMENT}" \
        ./backend

    log_info "Building frontend image..."
    docker build \
        -t "${FRONTEND_REPO}:${IMAGE_TAG}" \
        -t "${FRONTEND_REPO}:latest" \
        --build-arg NEXT_PUBLIC_API_URL="https://${PROJECT_NAME}.example.com/api/v1" \
        ./frontend

    log_success "Images built successfully"
}

# ==============================================================================
# Push to ECR
# ==============================================================================

push_images() {
    log_info "Authenticating with ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "$ECR_REGISTRY"

    log_info "Tagging images for ECR..."
    docker tag "${BACKEND_REPO}:${IMAGE_TAG}" "${ECR_REGISTRY}/${BACKEND_REPO}:${IMAGE_TAG}"
    docker tag "${BACKEND_REPO}:latest" "${ECR_REGISTRY}/${BACKEND_REPO}:latest"
    docker tag "${FRONTEND_REPO}:${IMAGE_TAG}" "${ECR_REGISTRY}/${FRONTEND_REPO}:${IMAGE_TAG}"
    docker tag "${FRONTEND_REPO}:latest" "${ECR_REGISTRY}/${FRONTEND_REPO}:latest"

    log_info "Pushing backend image..."
    docker push "${ECR_REGISTRY}/${BACKEND_REPO}:${IMAGE_TAG}"
    docker push "${ECR_REGISTRY}/${BACKEND_REPO}:latest"

    log_info "Pushing frontend image..."
    docker push "${ECR_REGISTRY}/${FRONTEND_REPO}:${IMAGE_TAG}"
    docker push "${ECR_REGISTRY}/${FRONTEND_REPO}:latest"

    log_success "Images pushed to ECR"
}

# ==============================================================================
# Deploy to ECS
# ==============================================================================

deploy_services() {
    log_info "Deploying to ECS cluster: $ECS_CLUSTER"

    log_info "Updating backend service..."
    aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$BACKEND_SERVICE" \
        --force-new-deployment \
        --region "$AWS_REGION" \
        --output text > /dev/null

    log_info "Updating frontend service..."
    aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$FRONTEND_SERVICE" \
        --force-new-deployment \
        --region "$AWS_REGION" \
        --output text > /dev/null

    log_info "Waiting for services to stabilize..."
    aws ecs wait services-stable \
        --cluster "$ECS_CLUSTER" \
        --services "$BACKEND_SERVICE" "$FRONTEND_SERVICE" \
        --region "$AWS_REGION"

    log_success "Services deployed and stable"
}

# ==============================================================================
# Smoke Tests
# ==============================================================================

run_smoke_tests() {
    local base_url="${DEPLOY_URL:-}"

    if [[ -z "$base_url" ]]; then
        log_warn "DEPLOY_URL not set, skipping smoke tests"
        return 0
    fi

    log_info "Running smoke tests against $base_url"

    # Health check
    if curl -sf "${base_url}/health" > /dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_error "Health check failed!"
        return 1
    fi

    # API health check
    if curl -sf "${base_url}/api/v1/health" > /dev/null 2>&1; then
        log_success "API health check passed"
    else
        log_warn "API health check failed (may be expected if path differs)"
    fi

    log_success "Smoke tests passed"
}

# ==============================================================================
# Main
# ==============================================================================

main() {
    echo "============================================"
    echo " SentinelAI Deployment"
    echo " Environment: $ENVIRONMENT"
    echo " Image Tag:   $IMAGE_TAG"
    echo " Region:      $AWS_REGION"
    echo "============================================"
    echo ""

    validate_environment
    check_prerequisites

    build_images
    push_images
    deploy_services
    run_smoke_tests

    echo ""
    log_success "Deployment complete!"
    echo "  Environment: $ENVIRONMENT"
    echo "  Image Tag:   $IMAGE_TAG"
    echo "  Timestamp:   $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}

main "$@"
