#!/bin/bash
set -e

# Local Build and Test Script for Llama Stack Documentation
# Simplified version - legacy docs are already in place

echo "🚀 Starting local Llama Stack documentation build..."

# Configuration
TEMP_DIR=$(mktemp -d)
REPO_URL="https://github.com/llamastack/llama-stack.git"
DOCS_DIR="$(pwd)/docs"

cleanup() {
    echo "🧹 Cleaning up temporary directory..."
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Step 1: Clone llama-stack repository
echo "📥 Cloning llama-stack repository..."
git clone "$REPO_URL" "$TEMP_DIR/llama-stack"
echo "✅ Repository cloned"

# Step 2: Install dependencies
echo "📦 Installing Docusaurus dependencies..."
cd "$TEMP_DIR/llama-stack/docs"
npm ci
echo "✅ Dependencies installed"

# Step 3: Apply configuration patches
echo "⚙️ Applying Docusaurus configuration patches..."

# Create versioning files
cat > "$TEMP_DIR/llama-stack/docs/versionsArchived.json" << 'EOF'
{
  "v0.2.22": "https://llamastack.github.io/legacy/v0.2.22/",
  "v0.2.21": "https://llamastack.github.io/legacy/v0.2.21/",
  "v0.2.20": "https://llamastack.github.io/legacy/v0.2.20/",
  "v0.2.19": "https://llamastack.github.io/legacy/v0.2.19/",
  "v0.2.18": "https://llamastack.github.io/legacy/v0.2.18/",
  "v0.2.17": "https://llamastack.github.io/legacy/v0.2.17/",
  "v0.2.16": "https://llamastack.github.io/legacy/v0.2.16/",
  "v0.2.15": "https://llamastack.github.io/legacy/v0.2.15/",
  "v0.2.14": "https://llamastack.github.io/legacy/v0.2.14/",
  "v0.2.13": "https://llamastack.github.io/legacy/v0.2.13/",
  "v0.2.12": "https://llamastack.github.io/legacy/v0.2.12/",
  "v0.2.11": "https://llamastack.github.io/legacy/v0.2.11/"
}
EOF

cat > "$TEMP_DIR/llama-stack/docs/versions.json" << 'EOF'
[]
EOF

# Patch docusaurus.config.ts
echo "🔧 Patching Docusaurus configuration..."

# Apply comprehensive patches to docusaurus.config.ts
cat > "$TEMP_DIR/config-patch.js" << 'EOF'
const fs = require('fs');
const path = require('path');

const configPath = process.argv[2];
let config = fs.readFileSync(configPath, 'utf8');

// Add archived versions loading at the top
const versioningImports = `
// Import archived versions configuration
const fs = require('fs');
const path = require('path');

// Load archived versions
const versionsArchived = (() => {
  try {
    return JSON.parse(fs.readFileSync(path.join(__dirname, 'versionsArchived.json'), 'utf8'));
  } catch (e) {
    console.warn('Could not load versionsArchived.json:', e);
    return {};
  }
})();

// Create dropdown items for archived versions
const archivedVersionsDropdownItems = Object.entries(versionsArchived).map(
  ([versionName, versionUrl]) => ({
    label: versionName,
    href: versionUrl,
  })
);
`;

// Insert versioning imports after existing imports
config = config.replace(
  /import type \* as OpenApiPlugin from "docusaurus-plugin-openapi-docs";/,
  `import type * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";

${versioningImports}`
);

// Change version label from "Next 🚧" to "Latest"
config = config.replace(
  /label: 'Next 🚧'/,
  "label: 'Latest'"
);

// Add versioning configuration to docs config
config = config.replace(
  /docItemComponent: "@theme\/ApiItem", \/\/ Derived from docusaurus-theme-openapi/,
  `docItemComponent: "@theme/ApiItem", // Derived from docusaurus-theme-openapi

          // Versioning configuration
          lastVersion: 'current',
          versions: {
            current: {
              label: 'Latest',
              path: '',
            },
          },

          // Only include current version since we handle archived versions separately
          onlyIncludeVersions: ['current'],`
);

// Add version dropdown to navbar items (position it on the right before GitHub)
const versionDropdown = `        {
          href: 'https://github.com/llamastack/llama-stack',
          label: 'GitHub',
          position: 'right',
        },
        // Version dropdown with archived versions
        {
          type: 'docsVersionDropdown',
          position: 'right',
          dropdownItemsAfter: archivedVersionsDropdownItems.length > 0 ? [
            {
              type: 'html',
              value: '<hr class="dropdown-separator">',
            },
            {
              type: 'html',
              className: 'dropdown-archived-versions',
              value: '<b>Archived versions</b>',
            },
            ...archivedVersionsDropdownItems,
            {
              type: 'html',
              value: '<hr class="dropdown-separator">',
            },
            {
              to: '/versions',
              label: 'All versions',
            },
          ] : [],
        },`;

// Replace GitHub item with version dropdown + GitHub
config = config.replace(
  /        {\s*href: 'https:\/\/github\.com\/llamastack\/llama-stack',\s*label: 'GitHub',\s*position: 'right',\s*},/,
  versionDropdown
);

fs.writeFileSync(configPath, config);
console.log('✅ Docusaurus configuration patched successfully');
EOF

node "$TEMP_DIR/config-patch.js" "$TEMP_DIR/llama-stack/docs/docusaurus.config.ts"

echo "✅ Configuration patches applied"

# Step 4: Generate API documentation
echo "📚 Generating API documentation..."
npm run gen-api-docs all
echo "✅ API docs generated"

# Step 5: Build Docusaurus site
echo "🏗️ Building Docusaurus site..."
npm run build
echo "✅ Docusaurus build completed"

# Step 6: Deploy to docs directory (preserve legacy and .git)
echo "🗂️ Deploying Docusaurus build..."

# Smart deployment: clear everything except legacy, .git, and .nojekyll
find "$DOCS_DIR" -mindepth 1 -maxdepth 1 ! -name 'legacy' ! -name '.git' ! -name '.nojekyll' -exec rm -rf {} +

# Copy Docusaurus build output
cp -r "$TEMP_DIR/llama-stack/docs/build/"* "$DOCS_DIR/"

# Ensure .nojekyll exists (in case it didn't exist before)
touch "$DOCS_DIR/.nojekyll"

echo "✅ Docusaurus content deployed"

# Step 7: Create versioning configuration files in deployed site
echo "⚙️ Setting up versioning configuration files..."

# Copy versioning files to deployment
cp "$TEMP_DIR/llama-stack/docs/versionsArchived.json" "$DOCS_DIR/"
cp "$TEMP_DIR/llama-stack/docs/versions.json" "$DOCS_DIR/"

echo "✅ Versioning files created"

# Step 8: Verify deployment structure
echo "🔍 Verifying deployment structure..."

echo "Contents of docs directory:"
ls -la "$DOCS_DIR/" | head -10

echo -e "\nLegacy versions:"
ls -la "$DOCS_DIR/legacy/" 2>/dev/null | head -5 || echo "❌ Legacy directory missing"

echo -e "\nVersioning files:"
[ -f "$DOCS_DIR/versionsArchived.json" ] && echo "✅ versionsArchived.json exists" || echo "❌ versionsArchived.json missing"
[ -f "$DOCS_DIR/versions.json" ] && echo "✅ versions.json exists" || echo "❌ versions.json missing"

echo -e "\n✅ Structure verification complete"

# Step 9: Start local server for testing
echo "🌐 Starting local development server..."
echo "📍 Your documentation is available at: http://localhost:3000"
echo "🔗 Main docs: http://localhost:3000/docs.html"
echo "📚 API Reference: http://localhost:3000/docs/api/llama-stack-specification"
echo "📚 Legacy versions: http://localhost:3000/legacy/"
echo ""
echo "Press Ctrl+C to stop the server"

cd "$DOCS_DIR"
python3 -m http.server 3000 2>/dev/null || python -m SimpleHTTPServer 3000
