// Dynamically load version information from versions.json
(function() {
    // Determine the current version from the URL path
    function getCurrentVersionFromPath() {
        const path = window.location.pathname;
        const match = path.match(/\/(v\d+\.\d+\.\d+)\//);
        if (match) {
            return match[1];
        }
        // Check if we're in latest
        if (path.includes('/latest/')) {
            return 'latest';
        }
        return null;
    }

    // Load versions.json and initialize the version selector
    function initializeVersionSelector() {
        const currentVersion = getCurrentVersionFromPath();

        // Fetch the versions.json file from the root
        fetch('/versions.json')
            .then(response => response.json())
            .then(data => {
                // Transform versions.json format to RTD format
                const rtdVersions = {
                    active: data.versions.map(v => ({
                        slug: v.name,
                        urls: {
                            documentation: v.url
                        }
                    })),
                    current: {
                        slug: currentVersion || data.versions.find(v => v.preferred)?.name || 'latest'
                    }
                };

                // Create the RTD-compatible version data
                const versionData = {
                    versions: rtdVersions,
                    projects: {
                        current: {
                            slug: 'llama-stack',
                            urls: {
                                home: 'https://github.com/llamastack/llama-stack',
                                builds: 'https://github.com/llamastack/llama-stack/actions',
                                downloads: 'https://github.com/llamastack/llama-stack/releases'
                            }
                        },
                        translations: []
                    }
                };

                // Dispatch the RTD event that the theme expects
                const event = new CustomEvent('readthedocs-addons-data-ready', {
                    detail: {
                        data: () => versionData
                    }
                });

                document.dispatchEvent(event);
            })
            .catch(error => {
                console.error('Failed to load versions.json:', error);
                // Fall back to static version if dynamic loading fails
                initializeStaticVersions();
            });
    }

    // Fallback function with static versions (can be updated as needed)
    function initializeStaticVersions() {
        const currentVersion = getCurrentVersionFromPath();
        const versionData = {
            versions: {
                active: [
                    {"slug": "latest", "urls": {"documentation": "/latest/"}},
                    {"slug": "v0.2.18", "urls": {"documentation": "/v0.2.18/"}},
                    {"slug": "v0.2.17", "urls": {"documentation": "/v0.2.17/"}},
                    {"slug": "v0.2.16", "urls": {"documentation": "/v0.2.16/"}},
                    {"slug": "v0.2.15", "urls": {"documentation": "/v0.2.15/"}},
                    {"slug": "v0.2.14", "urls": {"documentation": "/v0.2.14/"}}
                ],
                current: {"slug": currentVersion || "latest"}
            },
            projects: {
                current: {
                    slug: 'llama-stack',
                    urls: {
                        home: 'https://github.com/llamastack/llama-stack',
                        builds: 'https://github.com/llamastack/llama-stack/actions',
                        downloads: 'https://github.com/llamastack/llama-stack/releases'
                    }
                },
                translations: []
            }
        };

        const event = new CustomEvent('readthedocs-addons-data-ready', {
            detail: {
                data: () => versionData
            }
        });

        document.dispatchEvent(event);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeVersionSelector);
    } else {
        initializeVersionSelector();
    }
})();
