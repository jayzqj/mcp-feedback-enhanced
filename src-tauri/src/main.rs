// Prevents additional console window on Windows in both debug and release, DO NOT REMOVE!!
#![cfg_attr(target_os = "windows", windows_subsystem = "windows")]

use tauri::{Builder, Manager};
use std::sync::Mutex;

// 全局狀態管理
static APP_STATE: Mutex<Option<tauri::AppHandle>> = Mutex::new(None);

/// Tauri 應用程式狀態
#[derive(Default)]
struct AppState {
    web_url: String,
    desktop_mode: bool,
}

/// 獲取 Web URL
#[tauri::command]
fn get_web_url(state: tauri::State<AppState>) -> String {
    state.web_url.clone()
}

/// 設置 Web URL
#[tauri::command]
fn set_web_url(url: String, _state: tauri::State<AppState>) {
    println!("設置 Web URL: {}", url);
}

/// 檢查是否為桌面模式
#[tauri::command]
fn is_desktop_mode(state: tauri::State<AppState>) -> bool {
    state.desktop_mode
}

/// 設置桌面模式
#[tauri::command]
fn set_desktop_mode(enabled: bool, _state: tauri::State<AppState>) {
    println!("設置桌面模式: {}", enabled);
}

fn main() {
    // 初始化日誌
    env_logger::init();

    println!("正在啟動 MCP Feedback Enhanced 桌面應用程式...");

    // 創建 Tauri 應用程式
    Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState::default())
        .setup(|app| {
            // 儲存應用程式句柄到全局狀態
            {
                let mut state = APP_STATE.lock().unwrap();
                *state = Some(app.handle().clone());
            }

            // 獲取主視窗並設置高度為屏幕高度，寬度保持合理比例
            if let Some(window) = app.get_webview_window("main") {
                // 獲取主顯示器信息
                if let Ok(monitor) = window.primary_monitor() {
                    if let Some(monitor) = monitor {
                        let screen_size = monitor.size();
                        println!("檢測到屏幕尺寸: {}x{}", screen_size.width, screen_size.height);

                        // 設置窗口高度為屏幕高度，寬度保持合理比例（約1200-1400px）
                        let window_width = std::cmp::min(1400, (screen_size.width as f64 * 0.75) as u32);
                        let window_height = screen_size.height;

                        let _ = window.set_size(tauri::Size::Physical(tauri::PhysicalSize {
                            width: window_width,
                            height: window_height,
                        }));

                        // 計算居中位置
                        let center_x = (screen_size.width - window_width) / 2;
                        let center_y = (screen_size.height - window_height) / 2;

                        // 將窗口移動到屏幕中央
                        let _ = window.set_position(tauri::Position::Physical(tauri::PhysicalPosition {
                            x: center_x as i32,
                            y: center_y as i32,
                        }));

                        println!("窗口已設置為: 寬度{}px, 高度{}px (屏幕高度), 位置({}, {})",
                                window_width, window_height, center_x, center_y);
                    }
                }
            }

            // 檢查是否有 MCP_WEB_URL 環境變數
            if let Ok(web_url) = std::env::var("MCP_WEB_URL") {
                println!("檢測到 Web URL: {}", web_url);

                // 獲取主視窗並導航到 Web URL
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.navigate(web_url.parse().unwrap());
                }
            }

            println!("Tauri 應用程式已初始化");
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_web_url,
            set_web_url,
            is_desktop_mode,
            set_desktop_mode
        ])
        .run(tauri::generate_context!())
        .expect("運行 Tauri 應用程式時發生錯誤");
}
