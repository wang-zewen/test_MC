// ============================================
// 超强浏览器反检测脚本
// 针对Cloudflare等高级反爬虫系统
// ============================================

(() => {
    'use strict';

    // 1. 移除WebDriver标志
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });

    // 2. 修复Chrome对象
    if (!window.chrome) {
        window.chrome = {};
    }

    window.chrome.runtime = {
        connect: () => {},
        sendMessage: () => {},
        OnInstalledReason: {
            CHROME_UPDATE: 'chrome_update',
            INSTALL: 'install',
            SHARED_MODULE_UPDATE: 'shared_module_update',
            UPDATE: 'update'
        },
        OnRestartRequiredReason: {
            APP_UPDATE: 'app_update',
            OS_UPDATE: 'os_update',
            PERIODIC: 'periodic'
        },
        PlatformArch: {
            ARM: 'arm',
            ARM64: 'arm64',
            MIPS: 'mips',
            MIPS64: 'mips64',
            X86_32: 'x86-32',
            X86_64: 'x86-64'
        },
        PlatformNaclArch: {
            ARM: 'arm',
            MIPS: 'mips',
            MIPS64: 'mips64',
            X86_32: 'x86-32',
            X86_64: 'x86-64'
        },
        PlatformOs: {
            ANDROID: 'android',
            CROS: 'cros',
            LINUX: 'linux',
            MAC: 'mac',
            OPENBSD: 'openbsd',
            WIN: 'win'
        },
        RequestUpdateCheckStatus: {
            NO_UPDATE: 'no_update',
            THROTTLED: 'throttled',
            UPDATE_AVAILABLE: 'update_available'
        }
    };

    window.chrome.loadTimes = function() {
        return {
            commitLoadTime: Date.now() / 1000 - Math.random() * 10,
            connectionInfo: 'h2',
            finishDocumentLoadTime: Date.now() / 1000 - Math.random() * 5,
            finishLoadTime: Date.now() / 1000 - Math.random() * 3,
            firstPaintAfterLoadTime: Date.now() / 1000 - Math.random() * 2,
            firstPaintTime: Date.now() / 1000 - Math.random() * 3,
            navigationType: 'Other',
            npnNegotiatedProtocol: 'h2',
            requestTime: Date.now() / 1000 - Math.random() * 10,
            startLoadTime: Date.now() / 1000 - Math.random() * 8,
            wasAlternateProtocolAvailable: false,
            wasFetchedViaSpdy: true,
            wasNpnNegotiated: true
        };
    };

    window.chrome.csi = function() {
        return {
            onloadT: Date.now(),
            pageT: Date.now() - Math.random() * 1000,
            startE: Date.now() - Math.random() * 2000,
            tran: 15
        };
    };

    window.chrome.app = {
        isInstalled: false,
        InstallState: {
            DISABLED: 'disabled',
            INSTALLED: 'installed',
            NOT_INSTALLED: 'not_installed'
        },
        RunningState: {
            CANNOT_RUN: 'cannot_run',
            READY_TO_RUN: 'ready_to_run',
            RUNNING: 'running'
        }
    };

    // 3. 修复Plugins (更真实的插件列表)
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            const plugins = [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin},
                    description: "",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                },
                {
                    0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable", enabledPlugin: Plugin},
                    1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable", enabledPlugin: Plugin},
                    description: "",
                    filename: "internal-nacl-plugin",
                    length: 2,
                    name: "Native Client"
                }
            ];

            // 添加数组方法
            plugins.item = function(index) { return this[index] || null; };
            plugins.namedItem = function(name) {
                return this.find(p => p.name === name) || null;
            };
            plugins.refresh = function() {};

            return plugins;
        }
    });

    // 4. 修复语言
    Object.defineProperty(navigator, 'languages', {
        get: () => ['zh-CN', 'zh', 'en-US', 'en']
    });

    // 5. 修复平台信息
    Object.defineProperty(navigator, 'platform', {
        get: () => 'Linux x86_64'
    });

    // 6. 修复hardwareConcurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8
    });

    // 7. 修复deviceMemory
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8
    });

    // 8. 修复maxTouchPoints
    Object.defineProperty(navigator, 'maxTouchPoints', {
        get: () => 0
    });

    // 9. 修复vendor
    Object.defineProperty(navigator, 'vendor', {
        get: () => 'Google Inc.'
    });

    // 10. 修复productSub
    Object.defineProperty(navigator, 'productSub', {
        get: () => '20030107'
    });

    // 11. 修复vendorSub
    Object.defineProperty(navigator, 'vendorSub', {
        get: () => ''
    });

    // 12. 增强Permissions API
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => {
        if (parameters.name === 'notifications') {
            return Promise.resolve({state: Notification.permission});
        }
        return originalQuery(parameters);
    };

    // 13. 修复Canvas指纹（添加噪声）
    const toBlob = HTMLCanvasElement.prototype.toBlob;
    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
    const getImageData = CanvasRenderingContext2D.prototype.getImageData;

    // 噪声生成器
    const noisify = function(canvas, context) {
        const shift = {
            'r': Math.floor(Math.random() * 10) - 5,
            'g': Math.floor(Math.random() * 10) - 5,
            'b': Math.floor(Math.random() * 10) - 5,
            'a': Math.floor(Math.random() * 10) - 5
        };

        const width = canvas.width;
        const height = canvas.height;
        const imageData = getImageData.apply(context, [0, 0, width, height]);

        for (let i = 0; i < height; i++) {
            for (let j = 0; j < width; j++) {
                const n = ((i * (width * 4)) + (j * 4));
                imageData.data[n + 0] = imageData.data[n + 0] + shift.r;
                imageData.data[n + 1] = imageData.data[n + 1] + shift.g;
                imageData.data[n + 2] = imageData.data[n + 2] + shift.b;
                imageData.data[n + 3] = imageData.data[n + 3] + shift.a;
            }
        }

        context.putImageData(imageData, 0, 0);
    };

    Object.defineProperty(HTMLCanvasElement.prototype, 'toBlob', {
        value: function() {
            noisify(this, this.getContext('2d'));
            return toBlob.apply(this, arguments);
        }
    });

    Object.defineProperty(HTMLCanvasElement.prototype, 'toDataURL', {
        value: function() {
            noisify(this, this.getContext('2d'));
            return toDataURL.apply(this, arguments);
        }
    });

    Object.defineProperty(CanvasRenderingContext2D.prototype, 'getImageData', {
        value: function() {
            noisify(this.canvas, this);
            return getImageData.apply(this, arguments);
        }
    });

    // 14. 修复WebGL指纹
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        // UNMASKED_VENDOR_WEBGL
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        // UNMASKED_RENDERER_WEBGL
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
        return getParameter.apply(this, arguments);
    };

    // 15. 修复AudioContext指纹
    const audioCtx = window.AudioContext || window.webkitAudioContext;
    if (audioCtx) {
        const OriginalAudioContext = audioCtx;
        window.AudioContext = function() {
            const ctx = new OriginalAudioContext();
            const originalGetChannelData = AudioBuffer.prototype.getChannelData;

            AudioBuffer.prototype.getChannelData = function() {
                const channelData = originalGetChannelData.apply(this, arguments);
                for (let i = 0; i < channelData.length; i += 100) {
                    channelData[i] = channelData[i] + Math.random() * 0.0000001;
                }
                return channelData;
            };

            return ctx;
        };
    }

    // 16. 修复Screen分辨率
    Object.defineProperty(window.screen, 'availWidth', {
        get: () => 1920
    });
    Object.defineProperty(window.screen, 'availHeight', {
        get: () => 1080
    });
    Object.defineProperty(window.screen, 'width', {
        get: () => 1920
    });
    Object.defineProperty(window.screen, 'height', {
        get: () => 1080
    });
    Object.defineProperty(window.screen, 'colorDepth', {
        get: () => 24
    });
    Object.defineProperty(window.screen, 'pixelDepth', {
        get: () => 24
    });

    // 17. 隐藏自动化痕迹
    delete navigator.__proto__.webdriver;

    // 18. 修复时间精度（防止高精度计时检测）
    const originalPerformanceNow = performance.now;
    const randomOffset = Math.random() * 100;
    performance.now = function() {
        return originalPerformanceNow.apply(this, arguments) + randomOffset;
    };

    // 19. 修复Date精度
    const originalDate = Date;
    Date = new Proxy(originalDate, {
        construct: function(target, args) {
            if (args.length === 0) {
                return new target(originalDate.now() + Math.random() * 10);
            }
            return new target(...args);
        }
    });
    Date.now = function() {
        return originalDate.now() + Math.random() * 10;
    };
    Date.parse = originalDate.parse;
    Date.UTC = originalDate.UTC;

    // 20. 移除Headless特征
    Object.defineProperty(navigator, 'headless', {
        get: () => false
    });

    // 21. 修复iframe检测
    Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
        get: function() {
            return window;
        }
    });

    // 22. 修复Battery API（如果存在）
    if (navigator.getBattery) {
        navigator.getBattery = () => Promise.resolve({
            charging: true,
            chargingTime: 0,
            dischargingTime: Infinity,
            level: 1,
            addEventListener: () => {},
            removeEventListener: () => {},
            dispatchEvent: () => true
        });
    }

    // 23. 修复Connection API
    Object.defineProperty(navigator, 'connection', {
        get: () => ({
            downlink: 10,
            effectiveType: '4g',
            onchange: null,
            rtt: 50,
            saveData: false
        })
    });

    // 24. 隐藏Selenium/WebDriver痕迹
    ['$cdc_', '$wdc_', '__webdriver_', '__driver_', '__selenium_', '__fxdriver_', '__cypress_'].forEach(prop => {
        delete window[prop];
        delete document[prop];
    });

    // 25. 修复toString检测
    const originalToString = Function.prototype.toString;
    Function.prototype.toString = function() {
        if (this === window.chrome.runtime.connect ||
            this === window.chrome.runtime.sendMessage ||
            this === navigator.getBattery) {
            return 'function () { [native code] }';
        }
        return originalToString.apply(this, arguments);
    };

    // 26. 修复Object.getOwnPropertyDescriptor检测
    const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
    Object.getOwnPropertyDescriptor = function(obj, prop) {
        const descriptor = originalGetOwnPropertyDescriptor(obj, prop);
        if (descriptor && descriptor.get && descriptor.get.toString().includes('[native code]')) {
            descriptor.get = new Proxy(descriptor.get, {
                apply: function(target, thisArg, argumentsList) {
                    return Reflect.apply(target, thisArg, argumentsList);
                }
            });
        }
        return descriptor;
    };

    // 27. 添加真实的错误堆栈
    Error.stackTraceLimit = 10;

    console.log('✓ 超强反检测脚本已加载');
})();
