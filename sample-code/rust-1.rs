use crate::window::WindowCtx;
use std::f64::consts::TAU;

/// Trait for objects that can be drawn on a canvas.
///
/// Types implementing this trait can be rendered to a canvas by calling
/// the `draw` method with a `WindowCtx` providing access to the canvas
/// rendering context.
pub trait Draw {
    fn draw(&self, window: &WindowCtx);
}

/// Trait for objects that can be styled.
///
/// Types implementing this trait can be wrapped with styling information
/// via the `styled` method, which returns a `Styled<Self>` wrapper that
/// allows applying fill and stroke styles to the drawable.
pub trait Style: Draw + Sized {
    /// Wraps this drawable in a `Styled` wrapper to apply styling.
    ///
    /// Returns a new `Styled` instance that can be configured with fill and stroke styles.
    fn styled(self) -> Styled<Self> {
        Styled::new(self)
    }
}

/// A filled circle drawable.
///
/// Represents a circle defined by its center coordinates and radius.
/// The circle is filled using the current fill style of the canvas context.
///
/// # Fields
/// * `0` - A tuple `(x, y)` representing the center coordinates.
/// * `1` - The radius of the circle.
pub struct FilledCircle(pub (f64, f64), pub f64);

impl Draw for FilledCircle {
    /// Draws a filled circle at the specified center and radius.
    ///
    /// The circle is drawn using the current fill style of the canvas context.
    fn draw(&self, window: &WindowCtx) {
        let Self((x, y), r) = self;
        window.ctx.begin_path();
        window.ctx.arc(*x, *y, *r, 0.0, TAU).unwrap();
        window.ctx.fill();
    }
}

impl Style for FilledCircle {}

/// A line segment drawable.
///
/// Represents a line from one point to another.
/// The line is stroked using the current stroke style of the canvas context.
///
/// # Fields
/// * `0` - The x-coordinate of the starting point.
/// * `1` - The y-coordinate of the starting point.
/// * `2` - The x-coordinate of the ending point.
/// * `3` - The y-coordinate of the ending point.
pub struct Line(pub f64, pub f64, pub f64, pub f64);

impl Draw for Line {
    /// Draws a line segment between the two specified points.
    ///
    /// The line is stroked using the current stroke style of the canvas context.
    fn draw(&self, window: &WindowCtx) {
        let Self(x0, y0, x1, y1) = self;
        window.ctx.begin_path();
        window.ctx.move_to(*x0, *y0);
        window.ctx.line_to(*x1, *y1);
        window.ctx.stroke();
    }
}

impl Style for Line {}

/// A wrapper for applying styling to drawable objects.
///
/// This struct applies fill and stroke styles to any drawable object
/// without modifying the original. It uses the canvas context's save/restore
/// mechanism to ensure styles are properly scoped and don't affect other drawings.
///
/// # Type Parameters
/// * `C` - The contained drawable type.
pub struct Styled<C: Draw> {
    // Contained drawable
    contained: C,

    // Style Options
    fill: Option<String>,
    stroke: Option<String>,
}

/// Macro for generating style builder methods and an `apply_style` helper.
///
/// This macro generates:
/// - An `apply_style` method that applies all configured optional styles to the canvas
/// - Builder methods for each option that return `Self` for method chaining
///
/// # Arguments
/// - `$opt:ident` - The field name (e.g., `fill`, `stroke`)
/// - `$typ:ty` - The field type (e.g., `String`)
/// - `$ctxmethod:ident` - The canvas context method to call (e.g., `set_fill_style_str`)
///
/// # Example
/// ```ignore
/// handle_opts![
///     fill: String => set_fill_style_str,
///     stroke: String => set_stroke_style_str
/// ];
/// ```
macro_rules! handle_opts {
    ($($opt:ident: $typ:ty => $ctxmethod:ident),+) => {
        fn apply_style(&self, window: &WindowCtx) {
            $(
                if let Some($opt) = &self.$opt {
                    window.ctx.$ctxmethod(&$opt);
                }
            )+
        }
        $(
            pub fn $opt(self, value: $typ) -> Self {
                Self {
                    $opt: Some(value),
                    ..self
                }
            }
        )+
    };
}

impl<C: Draw> Styled<C> {
    /// Creates a new `Styled` wrapper with no styles applied.
    ///
    /// # Arguments
    /// * `contained` - The drawable object to wrap.
    fn new(contained: C) -> Self {
        Self {
            contained,
            fill: None,
            stroke: None,
        }
    }

    handle_opts![
        fill: String => set_fill_style_str,
        stroke: String => set_stroke_style_str
    ];
}

impl<C: Draw> Draw for Styled<C> {
    /// Draws the contained drawable with the specified fill and stroke styles applied.
    ///
    /// This method saves the current canvas state, applies the configured styles,
    /// draws the contained object, and then restores the canvas state.
    fn draw(&self, window: &WindowCtx) {
        window.ctx.save();
        self.apply_style(window);
        self.contained.draw(window);
        window.ctx.restore();
    }
}
