#!/bin/bash

# KIRA Automatic Deployment Script
# Deploys both Electron app and VitePress documentation.
#
# Usage:
#   ./deploy.sh                    # Use package.json version
#   ./deploy.sh 0.1.7              # Specify version
#   ./deploy.sh 0.1.7 --skip-notarize  # Skip notarization
#   ./deploy.sh --skip-notarize    # Current version + skip notarization

set -e  # Stop script on error

# AWS Region setting (S3 bucket: kira-releases)
export AWS_DEFAULT_REGION=ap-northeast-2

# Parse arguments
SKIP_NOTARIZE=false
VERSION_ARG=""

for arg in "$@"; do
  case $arg in
    --skip-notarize)
      SKIP_NOTARIZE=true
      ;;
    *)
      if [[ $arg =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        VERSION_ARG=$arg
      fi
      ;;
  esac
done

echo "🚀 Starting KIRA deployment..."
echo ""

# Navigate to project root directory
cd "$(dirname "$0")"

# ===========================
# 1. Version Setup
# ===========================
echo "📦 Step 1: Version Setup"
cd electron-app

if [ -n "$VERSION_ARG" ]; then
  npm version $VERSION_ARG --no-git-tag-version
  CURRENT_VERSION=$VERSION_ARG
  echo "   Specified version: $CURRENT_VERSION"
else
  CURRENT_VERSION=$(node -p "require('./package.json').version")
  echo "   Current version: $CURRENT_VERSION"
fi

if [ "$SKIP_NOTARIZE" = true ]; then
  echo "   ⚠️  Skipping notarization"
  export CSC_IDENTITY_AUTO_DISCOVERY=false
fi

echo ""
cd ..

# ===========================
# 2. Update Version in Documentation
# ===========================
echo "📝 Step 2: Update Version in Documentation"
# Replace only the version in download links (KIRA-X.X.X-arm64.dmg)
find vitepress-app -name "*.md" -exec sed -i '' -E "s/KIRA-[0-9]+\.[0-9]+\.[0-9]+-(universal|arm64)\.dmg/KIRA-$CURRENT_VERSION-arm64.dmg/g" {} \;
echo "   ✅ Documentation updated to version $CURRENT_VERSION"
echo ""

# ===========================
# 3. Build and Deploy Electron App (macOS)
# ===========================
echo "🔨 Step 3: Build and Deploy Electron App (macOS) to S3"
cd electron-app
npm run deploy
echo "   ✅ macOS app deployment complete"
echo ""

# ===========================
# 4. Build and Deploy Electron App (Windows)
# ===========================
echo "🔨 Step 4: Build and Deploy Electron App (Windows) to S3"
CSC_IDENTITY_AUTO_DISCOVERY=false npm run deploy:win
echo "   ✅ Windows app deployment complete"
echo ""
cd ..

# ===========================
# 5. Deploy VitePress Documentation
# ===========================
echo "📚 Step 5: Deploy VitePress Documentation"
cd vitepress-app
npm run docs:build
aws s3 sync .vitepress/dist s3://kira-releases --delete --exclude 'download/*' --exclude 'videos/*'
echo "   ✅ VitePress documentation deployment complete"
echo ""
cd ..

# ===========================
# 6. Invalidate CloudFront Cache
# ===========================
echo "🔄 Step 6: Invalidate CloudFront Cache"
aws cloudfront create-invalidation --distribution-id EU03W5ZNSG0E --paths "/*"
echo "   ✅ CloudFront cache invalidation complete"
echo ""

# ===========================
# Complete
# ===========================
echo "✨ Deployment complete!"
echo ""
echo "📦 Electron app (macOS): https://kira.krafton-ai.com/download/KIRA-$CURRENT_VERSION-arm64.dmg"
echo "📦 Electron app (Windows): https://kira.krafton-ai.com/download/KIRA-$CURRENT_VERSION.exe"
echo "📚 Documentation site: https://kira.krafton-ai.com"
echo ""
echo "🎉 Version $CURRENT_VERSION has been successfully deployed!"
