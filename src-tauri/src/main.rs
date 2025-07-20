// Prevents additional console window on Windows in both debug and release, DO NOT REMOVE!!
#![cfg_attr(target_os = "windows", windows_subsystem = "windows")]

use tauri::{Builder, Manager};
use std::sync::Mutex;

// 全局状态管理
static APP_STATE: Mutex<Option<tauri::AppHandle>> = Mutex::new(None);

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

            // 获取主视窗并设置尺寸
            if let Some(window) = app.get_webview_window("main") {
                // 获取主显示器信息
                if let Ok(monitor) = window.primary_monitor() {
                    if let Some(monitor) = monitor {
                        let screen_size = monitor.size();
                        let work_area = monitor.work_area();
                        println!("检测到屏幕尺寸: {}x{}", screen_size.width, screen_size.height);
                        println!("检测到工作区域: {}x{} at ({}, {})", 
                                work_area.size.width, work_area.size.height, work_area.position.x, work_area.position.y);

                        // 设置窗口宽度为屏幕宽度的90%，高度为工作区域的97%（留出边距确保内容完整显示）
                        let window_width = (screen_size.width as f64 * 0.9) as u32;
                        let window_height = (work_area.size.height as f64 * 0.97) as u32;

                        let _ = window.set_size(tauri::Size::Physical(tauri::PhysicalSize {
                            width: window_width,
                            height: window_height,
                        }));

                        // 计算居中位置（水平居中，垂直位置对齐工作区域顶部）
                        let center_x = (screen_size.width - window_width) / 2;
                        let pos_y = work_area.position.y;

                        // 将窗口移动到计算位置
                        let _ = window.set_position(tauri::Position::Physical(tauri::PhysicalPosition {
                            x: center_x as i32,
                            y: pos_y as i32,
                        }));

                        println!("窗口已设置为: 宽度{}px, 高度{}px (工作区域高度97%), 位置({}, {})",
                                window_width, window_height, center_x, pos_y);
                    }
                }
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
