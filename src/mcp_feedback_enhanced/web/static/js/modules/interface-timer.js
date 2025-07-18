/**
 * 界面时长计时器管理器
 * 用于记录和显示当前反馈界面的显示时长
 */
class InterfaceTimer {
    constructor() {
        this.startTime = null;
        this.timerInterval = null;
        this.isRunning = false;
        this.timerElement = null;
        this.retryCount = 0;
        this.maxRetries = 10;

        this.init();
    }

    /**
     * 初始化计时器
     */
    init() {
        console.log(`Attempting to initialize interface timer... (retry ${this.retryCount})`);

        this.timerElement = document.getElementById('interfaceTimer');
        if (!this.timerElement) {
            console.warn('Interface timer element not found');

            // 检查是否达到最大重试次数
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`Retrying in 500ms... (${this.retryCount}/${this.maxRetries})`);
                setTimeout(() => {
                    this.init();
                }, 500);
            } else {
                console.error('Failed to find interface timer element after maximum retries');
            }
            return;
        }

        console.log('Interface timer element found:', this.timerElement);
        console.log('Element parent:', this.timerElement.parentElement);
        console.log('Element visible:', this.timerElement.offsetParent !== null);

        // 设置开始时间为当前时间
        this.startTime = Date.now();
        console.log('Start time set to:', new Date(this.startTime));

        // 开始计时
        this.start();

        console.log('Interface timer initialized successfully');
    }

    /**
     * 开始计时
     */
    start() {
        if (this.isRunning) {
            return;
        }

        this.isRunning = true;
        
        // 立即更新一次显示
        this.updateDisplay();
        
        // 每秒更新一次
        this.timerInterval = setInterval(() => {
            this.updateDisplay();
        }, 1000);
        
        console.log('Interface timer started');
    }

    /**
     * 停止计时
     */
    stop() {
        if (!this.isRunning) {
            return;
        }

        this.isRunning = false;

        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }

        console.log('Interface timer stopped');
    }

    /**
     * 重置计时器
     */
    reset() {
        console.log('Resetting interface timer...');
        this.stop();
        this.startTime = Date.now();
        this.retryCount = 0;

        // 重新查找元素并启动
        this.timerElement = document.getElementById('interfaceTimer');
        if (this.timerElement) {
            console.log('Timer element found during reset');
            this.start();
        } else {
            console.warn('Timer element not found during reset, reinitializing...');
            this.init();
        }

        console.log('Interface timer reset completed');
    }

    /**
     * 重置计时器
     */
    reset() {
        this.stop();
        this.startTime = Date.now();
        this.updateDisplay();
        this.start();
        
        console.log('Interface timer reset');
    }

    /**
     * 更新显示
     */
    updateDisplay() {
        if (!this.timerElement) {
            console.warn('Timer element not found in updateDisplay');
            return;
        }

        if (!this.startTime) {
            console.warn('Start time not set in updateDisplay');
            return;
        }

        const currentTime = Date.now();
        const elapsedTime = Math.floor((currentTime - this.startTime) / 1000); // 转换为秒

        const minutes = Math.floor(elapsedTime / 60);
        const seconds = elapsedTime % 60;

        // 格式化为 mm:ss
        const formattedTime = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        // 更新显示
        const oldText = this.timerElement.textContent;
        this.timerElement.textContent = formattedTime;

        // 只在第一次更新或每10秒输出一次日志，避免日志过多
        if (elapsedTime === 0 || elapsedTime % 10 === 0) {
            console.log(`Timer updated: ${oldText} -> ${formattedTime} (elapsed: ${elapsedTime}s)`);
        }
    }

    /**
     * 获取当前经过的时间（秒）
     */
    getElapsedTime() {
        if (!this.startTime) {
            return 0;
        }
        
        return Math.floor((Date.now() - this.startTime) / 1000);
    }

    /**
     * 获取格式化的时间字符串
     */
    getFormattedTime() {
        const elapsedTime = this.getElapsedTime();
        const minutes = Math.floor(elapsedTime / 60);
        const seconds = elapsedTime % 60;
        
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    /**
     * 销毁计时器
     */
    destroy() {
        this.stop();
        this.startTime = null;
        this.timerElement = null;
        
        console.log('Interface timer destroyed');
    }
}

// 导出类
window.InterfaceTimer = InterfaceTimer;

// 页面加载完成后自动初始化
document.addEventListener('DOMContentLoaded', () => {
    // 等待更长时间确保所有元素都已加载，特别是动态内容
    setTimeout(() => {
        if (!window.interfaceTimer) {
            window.interfaceTimer = new InterfaceTimer();
        }
    }, 1000);
});

// 也可以通过全局函数手动初始化
window.initInterfaceTimer = () => {
    console.log('Manual interface timer initialization requested');

    // 清理现有的计时器
    if (window.interfaceTimer) {
        console.log('Cleaning up existing InterfaceTimer...');
        try {
            window.interfaceTimer.destroy();
        } catch (e) {
            console.warn('Error destroying existing timer:', e);
        }
        window.interfaceTimer = null;
    }

    // 创建新的计时器实例
    console.log('Creating new InterfaceTimer instance');
    try {
        window.interfaceTimer = new InterfaceTimer();
        console.log('InterfaceTimer created successfully');
    } catch (e) {
        console.error('Error creating InterfaceTimer:', e);
    }
};

// 强制启动计时器的全局函数（用于调试）
window.forceStartTimer = () => {
    console.log('Force starting timer...');
    const element = document.getElementById('interfaceTimer');
    if (!element) {
        console.error('Timer element not found!');
        return;
    }

    console.log('Timer element found:', element);

    // 创建一个简单的计时器
    let startTime = Date.now();
    let interval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const formatted = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        element.textContent = formatted;
        console.log('Force timer update:', formatted);
    }, 1000);

    window.forceTimerInterval = interval;
    console.log('Force timer started');
};

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (window.interfaceTimer) {
        window.interfaceTimer.destroy();
    }
});
