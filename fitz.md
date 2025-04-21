get_textbox(rect, textpage=None)
Retrieve the text contained in a rectangle.

Parameters:
rect (rect-like) – rect-like.

textpage – a TextPage to use. If omitted, a new, temporary textpage will be created.

Returns:
a string with interspersed linebreaks where necessary. It is based on dedicated code (changed in v1.19.0). A typical use is checking the result of Page.search_for():

rl = page.search_for("currency:")
page.get_textbox(rl[0])
'Currency:'

---

get_pixmap(*, matrix=pymupdf.Identity, dpi=None, colorspace=pymupdf.csRGB, clip=None, alpha=False, annots=True)
Create a pixmap from the page. This is probably the most often used method to create a Pixmap.

All parameters are keyword-only.

Parameters:
matrix (matrix_like) – default is Identity.

dpi (int) – desired resolution in x and y direction. If not None, the "matrix" parameter is ignored. (New in v1.19.2)

colorspace (str or Colorspace) – The desired colorspace, one of “GRAY”, “RGB” or “CMYK” (case insensitive). Or specify a Colorspace, ie. one of the predefined ones: csGRAY, csRGB or csCMYK.

clip (irect_like) – restrict rendering to the intersection of this area with the page’s rectangle.

alpha (bool) –

whether to add an alpha channel. Always accept the default False if you do not really need transparency. This will save a lot of memory (25% in case of RGB … and pixmaps are typically large!), and also processing time. Also note an important difference in how the image will be rendered: with True the pixmap’s samples area will be pre-cleared with 0x00. This results in transparent areas where the page is empty. With False the pixmap’s samples will be pre-cleared with 0xff. This results in white where the page has nothing to show.

Show/hide history
annots (bool) – (new in version 1.16.0) whether to also render annotations or to suppress them. You can create pixmaps for annotations separately.

Return type:
Pixmap

Returns:
Pixmap of the page. For fine-controlling the generated image, the by far most important parameter is matrix. E.g. you can increase or decrease the image resolution by using Matrix(xzoom, yzoom). If zoom > 1, you will get a higher resolution: zoom=2 will double the number of pixels in that direction and thus generate a 2 times larger image. Non-positive values will flip horizontally, resp. vertically. Similarly, matrices also let you rotate or shear, and you can combine effects via e.g. matrix multiplication. See the Matrix section to learn more.

Note

The pixmap will have “premultiplied” pixels if alpha=True. To learn about some background, e.g. look for “Premultiplied alpha” here.

The method will respect any page rotation and will not exceed the intersection of clip and Page.cropbox. If you need the page’s mediabox (and if this is a different rectangle), you can use a snippet like the following to achieve this:

In [1]: import pymupdf
In [2]: doc=pymupdf.open("demo1.pdf")
In [3]: page=doc[0]
In [4]: rotation = page.rotation
In [5]: cropbox = page.cropbox
In [6]: page.set_cropbox(page.mediabox)
In [7]: page.set_rotation(0)
In [8]: pix = page.get_pixmap()
In [9]: page.set_cropbox(cropbox)
In [10]: if rotation != 0:
   ...:     page.set_rotation(rotation)
   ...:
In [11]:


---

Rect
Rect represents a rectangle defined by four floating point numbers x0, y0, x1, y1. They are treated as being coordinates of two diagonally opposite points. The first two numbers are regarded as the “top left” corner P(x0,y0) and P(x1,y1) as the “bottom right” one. However, these two properties need not coincide with their intuitive meanings – read on.

The following remarks are also valid for IRect objects:

A rectangle in the sense of (Py-) MuPDF (and PDF) always has borders parallel to the x- resp. y-axis. A general orthogonal tetragon is not a rectangle – in contrast to the mathematical definition.

The constructing points can be (almost! – see below) anywhere in the plane – they need not even be different, and e.g. “top left” need not be the geometrical “north-western” point.

Units are in points, where 72 points is 1 inch.

For any given quadruple of numbers, the geometrically “same” rectangle can be defined in four different ways:
Rect(P(x0,y0), P(x1,y1))

Rect(P(x1,y1), P(x0,y0))

Rect(P(x0,y1), P(x1,y0))

Rect(P(x1,y0), P(x0,y1))

(Changed in v1.19.0) Hence some classification:

A rectangle is called valid if x0 <= x1 and y0 <= y1 (i.e. the bottom right point is “south-eastern” to the top left one), otherwise invalid. Of the four alternatives above, only the first is valid. Please take into account, that in MuPDF’s coordinate system, the y-axis is oriented from top to bottom. Invalid rectangles have been called infinite in earlier versions.

A rectangle is called empty if x0 >= x1 or y0 >= y1. This implies, that invalid rectangles are also always empty. And width (resp. height) is set to zero if x0 > x1 (resp. y0 > y1). In previous versions, a rectangle was empty only if one of width or height was zero.

Rectangle coordinates cannot be outside the number range from FZ_MIN_INF_RECT = -2147483648 to FZ_MAX_INF_RECT = 2147483520. Both values have been chosen, because they are the smallest / largest 32bit integers that survive C float conversion roundtrips. In previous versions there was no limit for coordinate values.

There is exactly one “infinite” rectangle, defined by x0 = y0 = FZ_MIN_INF_RECT and x1 = y1 = FZ_MAX_INF_RECT. It contains every other rectangle. It is mainly used for technical purposes – e.g. when a function call should ignore a formally required rectangle argument. This rectangle is not empty.

Rectangles are (semi-) open: The right and the bottom edges (including the resp. corners) are not considered part of the rectangle. This implies, that only the top-left corner (x0, y0) can ever belong to the rectangle - the other three corners never do. An empty rectangle contains no corners at all.


---

IRect
IRect is a rectangular bounding box, very similar to Rect, except that all corner coordinates are integers. IRect is used to specify an area of pixels, e.g. to receive image data during rendering. Otherwise, e.g. considerations concerning emptiness and validity of rectangles also apply to this class. Methods and attributes have the same names, and in many cases are implemented by re-using the respective Rect counterparts.

Attribute / Method

Short Description

IRect.contains()

checks containment of another object

IRect.get_area()

calculate rectangle area

IRect.intersect()

common part with another rectangle

IRect.intersects()

checks for non-empty intersection

IRect.morph()

transform with a point and a matrix

IRect.torect()

matrix that transforms to another rectangle

IRect.norm()

the Euclidean norm

IRect.normalize()

makes a rectangle finite

IRect.bottom_left

bottom left point, synonym bl

IRect.bottom_right

bottom right point, synonym br

IRect.height

height of the rectangle

IRect.is_empty

whether rectangle is empty

IRect.is_infinite

whether rectangle is infinite

IRect.rect

the Rect equivalent

IRect.top_left

top left point, synonym tl

IRect.top_right

top_right point, synonym tr

IRect.quad

Quad made from rectangle corners

IRect.width

width of the rectangle

IRect.x0

X-coordinate of the top left corner

IRect.x1

X-coordinate of the bottom right corner

IRect.y0

Y-coordinate of the top left corner

IRect.y1

Y-coordinate of the bottom right corner

Class API

class IRect
__init__(self)
__init__(self, x0, y0, x1, y1)
__init__(self, irect)
__init__(self, sequence)
Overloaded constructors. Also see example