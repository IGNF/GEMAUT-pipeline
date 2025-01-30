#ifndef TPOINT2D_HPP
#define TPOINT2D_HPP

// Generic template for TPoint2D to support different types like int, double, etc.
template <typename T>
struct TPoint2D {
    T x;
    T y;

    // Constructor for convenience
    TPoint2D() : x(0), y(0) {}
    TPoint2D(T xVal, T yVal) : x(xVal), y(yVal) {}
};

#endif // TPOINT2D_HPP
