// Prevents additional console window on Windows in both debug and release, DO NOT REMOVE!!
#![cfg_attr(target_os = "windows", windows_subsystem = "windows")]

use tauri::{Builder, Manager, PhysicalPosition, PhysicalSize, Position, Size};
use std::sync::Mutex;
use std::path::PathBuf;
use std::fs;
use serde::{Deserialize, Serialize};

// 全局状态管理
static APP_STATE: Mutex<Option<tauri::AppHandle>> = Mutex::new(None);

/// 窗口大小和位置配置
#[derive(Serialize, Deserialize, Debug, Clone)]
struct WindowConfig {
    width: u32,
    height: u32,
    x: i32,
    y: i32,
}

impl Default for WindowConfig {
    fn default() -> Self {
        Self {
            width: 1260,
            height: 850,
            x: 0,
            y: 0,
        }
    }
}

/// Tauri 应用程序状态
#[derive(Default)]
struct AppState {
    web_url: String,
    desktop_mode: bool,
}

/// 获取 Web URL
#[tauri::command]
fn get_web_url(state: tauri::State<AppState>) -> String {
    state.web_url.clone()
}

/// 设置 Web URL
#[tauri::command]
fn set_web_url(url: String, _state: tauri::State<AppState>) {
    println!("设置 Web URL: {}", url);
}

/// 检查是否为桌面模式
#[tauri::command]
fn is_desktop_mode(state: tauri::State<AppState>) -> bool {
    state.desktop_mode
}

/// 设置桌面模式
#[tauri::command]
fn set_desktop_mode(enabled: bool, _state: tauri::State<AppState>) {
    println!("设置桌面模式: {}", enabled);
}

/// 获取配置文件路径
fn get_config_path() -> Option<PathBuf> {
    dirs::config_dir().map(|mut path| {
        path.push("mcp-feedback-enhanced");
        path.push("window-config.json");
        path
    })
}

/// 保存窗口配置
fn save_window_config(config: &WindowConfig) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(config_path) = get_config_path() {
        // 确保目录存在
        if let Some(parent) = config_path.parent() {
            fs::create_dir_all(parent)?;
        }
        
        let json = serde_json::to_string_pretty(config)?;
        fs::write(&config_path, json)?;
        println!("窗口配置已保存到: {:?}", config_path);
    }
    Ok(())
}

/// 读取窗口配置
fn load_window_config() -> WindowConfig {
    if let Some(config_path) = get_config_path() {
        if config_path.exists() {
            match fs::read_to_string(&config_path) {
                Ok(content) => {
                    match serde_json::from_str::<WindowConfig>(&content) {
                        Ok(config) => {
                            println!("已加载窗口配置: {:?}", config);
                            return config;
                        }
                        Err(e) => {
                            println!("解析窗口配置失败: {}", e);
                        }
                    }
                }
                Err(e) => {
                    println!("读取窗口配置文件失败: {}", e);
                }
            }
        } else {
            println!("窗口配置文件不存在，使用默认配置");
        }
    }
    
    WindowConfig::default()
}

/// 计算默认窗口大小和位置
fn calculate_default_window_config(window: &tauri::WebviewWindow) -> Option<WindowConfig> {
    if let Ok(monitor) = window.primary_monitor() {
        if let Some(monitor) = monitor {
            let screen_size = monitor.size();
            let work_area = monitor.work_area();
            
            // 设置窗口宽度为屏幕宽度的90%，高度为工作区域的97%
            let window_width = (screen_size.width as f64 * 0.9) as u32;
            let window_height = (work_area.size.height as f64 * 0.97) as u32;
            
            // 计算居中位置
            let center_x = (screen_size.width - window_width) / 2;
            let pos_y = work_area.position.y;
            
            return Some(WindowConfig {
                width: window_width,
                height: window_height,
                x: center_x as i32,
                y: pos_y as i32,
            });
        }
    }
    None
}

/// 检查给定窗口配置是否位于任意显示器的工作区域内
fn is_config_on_any_monitor(app: &tauri::AppHandle, config: &WindowConfig) -> bool {
    let monitors = app.available_monitors().unwrap_or_default();
    let wx1 = config.x as i32;
    let wy1 = config.y as i32;
    let wx2 = wx1 + config.width as i32;
    let wy2 = wy1 + config.height as i32;

    for monitor in monitors {
        let area = monitor.work_area();
        let mx1 = area.position.x as i32;
        let my1 = area.position.y as i32;
        let mx2 = mx1 + area.size.width as i32;
        let my2 = my1 + area.size.height as i32;

        let intersects = wx1 < mx2 && wx2 > mx1 && wy1 < my2 && wy2 > my1;
        if intersects {
            return true;
        }
    }
    false
}

/// 如果窗口配置离屏，则回退到合适的默认配置
fn adjust_config_into_visible_area(
    app: &tauri::AppHandle,
    window: &tauri::WebviewWindow,
    config: &WindowConfig,
) -> WindowConfig {
    if is_config_on_any_monitor(app, config) {
        return config.clone();
    }

    if let Some(default_cfg) = calculate_default_window_config(window) {
        return default_cfg;
    }

    WindowConfig::default()
}

fn main() {
    // 初始化日誌
    env_logger::init();

    println!("正在启动 MCP Feedback Enhanced 桌面应用程序...");

    // 创建 Tauri 应用程序
    Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState::default())
        .setup(|app| {
            // 储存应用程序句柄到全局状态
            {
                let mut state = APP_STATE.lock().unwrap();
                *state = Some(app.handle().clone());
            }

            // 获取主视窗并设置尺寸 - 立即隐藏窗口以避免闪烁
            if let Some(window) = app.get_webview_window("main") {
                // 首先隐藏窗口
                let _ = window.hide();
                
                // 尝试加载保存的窗口配置
                let mut config = load_window_config();
                
                // 如果配置是默认值，说明没有保存的配置，需要计算合适的大小
                if config.width == 1260 && config.height == 850 && config.x == 0 && config.y == 0 {
                    if let Some(calculated_config) = calculate_default_window_config(&window) {
                        config = calculated_config;
                        // 保存新计算的配置
                        let _ = save_window_config(&config);
                    }
                }
                
                // 防止窗口位置离屏，必要时自动回退到可见区域
                let adjusted = adjust_config_into_visible_area(&app.handle(), &window, &config);
                if adjusted.x != config.x
                    || adjusted.y != config.y
                    || adjusted.width != config.width
                    || adjusted.height != config.height
                {
                    println!(
                        "检测到离屏或无效窗口配置，自动调整为: {:?}",
                        adjusted
                    );
                    config = adjusted;
                    let _ = save_window_config(&config);
                }
                
                // 应用窗口配置
                let _ = window.set_size(Size::Physical(PhysicalSize {
                    width: config.width,
                    height: config.height,
                }));
                
                let _ = window.set_position(Position::Physical(PhysicalPosition {
                    x: config.x,
                    y: config.y,
                }));
                
                println!("窗口已设置为: 宽度{}px, 高度{}px, 位置({}, {})",
                        config.width, config.height, config.x, config.y);
                
                // 等待一下确保设置生效，然后显示窗口
                std::thread::sleep(std::time::Duration::from_millis(100));
                let _ = window.show();
                
                // 监听窗口大小和位置变化事件
                let window_clone = window.clone();
                window.on_window_event(move |event| {
                    match event {
                        tauri::WindowEvent::Resized(_) | tauri::WindowEvent::Moved(_) => {
                            // 获取当前窗口大小和位置
                            if let (Ok(size), Ok(position)) = (window_clone.outer_size(), window_clone.outer_position()) {
                                let current_config = WindowConfig {
                                    width: size.width,
                                    height: size.height,
                                    x: position.x,
                                    y: position.y,
                                };
                                
                                // 同步保存配置，避免Tokio上下文问题
                                std::thread::spawn(move || {
                                    let _ = save_window_config(&current_config);
                                });
                            }
                        }
                        _ => {}
                    }
                });
            }

            // 检查是否有 MCP_WEB_URL 环境变量
            if let Ok(web_url) = std::env::var("MCP_WEB_URL") {
                println!("检测到 Web URL: {}", web_url);

                // 获取主视窗并导航到 Web URL
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.navigate(web_url.parse().unwrap());
                }
            }

            println!("Tauri 应用程序已初始化");
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_web_url,
            set_web_url,
            is_desktop_mode,
            set_desktop_mode
        ])
        .run(tauri::generate_context!())
        .expect("运行 Tauri 应用程序时发生错误");
}
