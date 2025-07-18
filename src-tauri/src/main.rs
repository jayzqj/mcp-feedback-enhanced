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
    // 初始化日志
    env_logger::init();

    println!("正在启动 MCP Feedback Enhanced 桌面应用程序...");

    // 创建 Tauri 应用程序
    Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState::default())
        .setup(|app| {
            // 保存应用程序句柄到全局状态
            {
                let mut state = APP_STATE.lock().unwrap();
                *state = Some(app.handle().clone());
            }

            // 检查是否有 MCP_WEB_URL 环境变量
            if let Ok(web_url) = std::env::var("MCP_WEB_URL") {
                println!("检测到 Web URL: {}", web_url);

                // 获取主窗口并导航到 Web URL
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
