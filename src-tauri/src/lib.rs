use pyo3::prelude::*;
use tauri::{Builder, Context, Manager};
use std::sync::Mutex;

// 全局状态管理
static APP_STATE: Mutex<Option<tauri::AppHandle>> = Mutex::new(None);

/// Tauri 应用程序状态
#[derive(Default)]
struct AppState {
    web_url: String,
    desktop_mode: bool,
}

/// 生成 Tauri 上下文
pub fn tauri_generate_context() -> Context {
    tauri::generate_context!()
}

/// 创建 Tauri 应用程序构建器
pub fn create_tauri_builder() -> Builder<tauri::Wry> {
    Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState::default())
        .setup(|app| {
            // 保存应用程序句柄到全局状态
            {
                let mut state = APP_STATE.lock().unwrap();
                *state = Some(app.handle().clone());
            }

            // 设置应用程序状态
            let _app_state = app.state::<AppState>();
            {
                // 这里可以设置初始状态
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
}

/// 获取 Web URL
#[tauri::command]
fn get_web_url(state: tauri::State<AppState>) -> String {
    state.web_url.clone()
}

/// 设置 Web URL
#[tauri::command]
fn set_web_url(url: String, _state: tauri::State<AppState>) {
    // 注意：这里需要使用内部可变性，但 tauri::State 不支持
    // 实际实现中可能需要使用 Mutex 或其他同步原语
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

/// PyO3 模块定义
#[pymodule]
#[pyo3(name = "ext_mod")]
pub mod ext_mod {
    use super::*;

    #[pymodule_init]
    fn init(module: &Bound<'_, PyModule>) -> PyResult<()> {
        // 注册 context_factory 函数
        module.add_function(wrap_pyfunction!(context_factory, module)?)?;

        // 注册 builder_factory 函数
        module.add_function(wrap_pyfunction!(builder_factory, module)?)?;

        // 注册 run_app 函数
        module.add_function(wrap_pyfunction!(run_app, module)?)?;

        Ok(())
    }

    /// 创建 Tauri 上下文的工厂函数
    #[pyfunction]
    fn context_factory() -> PyResult<String> {
        // 返回序列化的上下文信息
        // 实际实现中，这里应该返回可以被 Python 使用的上下文
        Ok("tauri_context".to_string())
    }

    /// 创建 Tauri 构建器的工厂函数
    #[pyfunction]
    fn builder_factory() -> PyResult<String> {
        // 返回序列化的构建器信息
        // 实际实现中，这里应该返回可以被 Python 使用的构建器
        Ok("tauri_builder".to_string())
    }

    /// 运行 Tauri 应用程序
    #[pyfunction]
    fn run_app(web_url: String) -> PyResult<i32> {
        println!("正在启动 Tauri 应用程序，Web URL: {}", web_url);

        // 创建并运行 Tauri 应用程序
        let _builder = create_tauri_builder();
        let _context = tauri_generate_context();

        // 在实际实现中，这里需要处理异步运行
        // 目前返回成功状态
        match std::thread::spawn(move || {
            // 这里应该运行 Tauri 应用程序
            // builder.run(context)
            println!("Tauri 应用程序线程已启动");
            0
        }).join() {
            Ok(code) => Ok(code),
            Err(_) => Ok(1),
        }
    }
}
