/// Logs formatted messages to the browser console.
///
/// This macro provides a convenient way to log debug information to the browser's
/// JavaScript console using the same syntax as Rust's `println!` and `format!` macros.
///
/// # Examples
/// ```ignore
/// console_log!("Hello, world!");
/// console_log!("Value: {}", 42);
/// console_log!("Multiple: {} and {}", "hello", "goodbye");
/// ```
/// Logs formatted messages to the browser console.
///
/// This macro provides a convenient way to log debug information to the browser's
/// JavaScript console using the same syntax as Rust's `println!` and `format!` macros.
///
/// # Examples
/// ```ignore
/// console_log!("Hello, world!");
/// console_log!("Value: {}", 42);
/// console_log!("Multiple: {} and {}", "hello", "goodbye");
/// ```
#[macro_export]
macro_rules! console_log {
    ($($t:tt)*) => {
        web_sys::console::log_1(&format!($($t)*).into())
    };
}
