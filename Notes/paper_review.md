# References Review

## Overview
* [R. Randiamahefa, *Printed Music Recognition*, 1993](#1993-1)
* [K. Todd Reed, *Automatic Computer Recognition of Printed Music*, 1996](#1996-1)
* [P. Bellini, *Optical Music Sheet Segmentation*, 2001](#2001-1)
* [H. Miyao, *Stave Extraction for Printed Music Scores*, 2002](#2002-1)
* [L. Pugin, *Optical Music Recognition of Early Typographic Prints using Hidden Markov Models*, 2006](#2006-1)
* [J. A. Burgoyne, *A Comparative Survey of Image Binarisation Algorithms for Optical Recognition on Degraded Musical Sources*, 2007](#2007-1)
* [A. Fornes, *Handwritten Symbol Recognition by a Boosted Blurred Shape Model with Error Correction*, 2007](#2007-2)
* [F. Rossant, *Robust and Adaptive OMR System Including Fuzzy Modeling, Fusion of Musical Rules, and Possible Error Detection*, 2007](#2007-3)
* [C. Dalitz, *A Comparative Study of Staff Removal Algorithms*, 2008](#2008-1)
* [Jaime dos Santos Cardoso, *Staff Detection with Stable Paths*, 2009](#2009-1)
* [A. Dutta, *An Efficient Staff Removal Approach from Printed Musical Documents*, 2010](#2010-1)
* [T. Pinto, *Music Score Binarization Based on Domain Knowledge*, 2011](#2011-1)
* [J. Liang, *Multi-line Fitting Using Two-Stage Iterative Adaptive Approach*, 2012](#2012-1)

<h1 id="1993-1"/>
### Printed Music Recognition

#### Segmentation
- Detection of stafflines
	- Horizontal projection (Y-projection)

		To compute the y-projection of the image and find its local maxima, it works based on several assumptions: the stafflines are perfectly horizontal, unbroken, and parallel to one another.
		
	- Hough transform
		1. Vertical projection (X-projection)
		2. Projection filtering
		3. Indicating local minima regions
		4. Horizontal projection (Y-projection) for each regions figured from last stage
		5. Clustering different peaks into several stafflines

		Stage 1, 2, and 3 are used for several reasons: 1) reducing computational loading, i.e. segmenting the original image into subimages that each probably contains only stafflines; 2) reducing interference for stafflines detection such as musical notation.
		
		After the first 3 stages, the segmented image should expectedly contains stafflines only that the horizontal projection indicates the positions of stafflines more accurately. Therefore, the local maxima of horizontal projection are extracted and then fit into a couple of lines with Hough transform.
		
	- Comments
		
		Both methods work only for images that stafflines are horizontally parallel, and they are not robust for images with rotation deformation.
		 
- Staff removal

	Removing rule depends on the thickness threshold, which is obtained by measuring the width of local maxima regions.

#### Construction of attributed graph representation
- Process after staff removal
- Polygonalization and skeletonization
- Minimum distance contour attribution

#### Recognition of notes with musical symbols
- Use attributed graph obtained by polygonalization

<h1 id="1996-1"/>
### Automatic Computer Recognition of Printed Music

#### Staff detection and removal
- Run-length coding
	
	Use RLC for detecting the region, also called **staff sample**, which contains five equally spaced black runs, clustering the detected regions and obtain the rotation angle with the median of stafflines.
	
- Deal with deformation

	Considering the defects of printed music scores, lines are not perfectly straight and equally thick. To keep the algorigthm robust, each staffline might be segmented into several line pieces that form as a curve.
	
- Remove stafflines with a threshold varied by thickness

#### Segmentation

- Identify connected components with line adjacency graphs

	Find all black runs along each row or column and connect the center points between adjacent and overlapped runs, which is called LAG.
	
- Compressed LAG

	Use criteria to merge connected edges of a group of nodes (black runs). Says node A and B:
	1. A is above B
	2. A has degree (a, 1) and B has degree (1, B)
	3. The run-lengths of A and B are roughly the same
	4. The connected nodes can be represented approximately by a straight line
	
	Note the degree of a node is the number of edges connected to each side, (above, below).
	
- Text removal

#### Music symbol recognition

- Lines and curves

	Use LAG to detect groups of adjacent edges that are roughly collinear to form a longer line.

- Accidentals, rests, and clefs

	Use character profiles that is similar to contour analysis.

- Note head recognition

	Use template matching on the original image (which is not applied staff removal), the template images consist of three types of pixels, namely foreground, background, or interior background.
	
	Template matching suffers from run time performance, so two-stage template matching is proposed.

#### Contextual recognition

- Graph representation

	It is a higher level representation of recognition, for providing the opportunity to improve recognition quality with music notation ruls.

<h1 id="2001-1"/>
### Optical Muscic Sheet Segmentation

- O3MR

	Object Oriented Optical Music Recognition, which recognizes music symbols by detecting and forming the basic structures.
	
#### Architecture
- Segmentation
- Basic symbol recognition
- Music notation model refinement

#### Segmentation

Quot: The music sheet image is analyzed and recursively split into smaller blocks by defining a set of horizontal and vertical cut lines that allow isolating/extracting basic symbols

- Level 0: Staff detection

	Use RLC to find stafflines information, then apply y-projection and T-profile that detects a regular pattern based on the characteristics of a staff.

- Level 1: Regions that contain music symbols indication

	Apply a binary function F that determines whether a region contains any symbol other than stafflines or not with sliding window. Then, each active region has symbols and the x-projection is obtained to detect note head. The method is called double thresholding: the peaks and the width of remaining peaks must be greater than threshold values. After note head detection, the other symbols such as accedentals can be figured out with x-projection as well. The rule determining the existence of symbols is also based on some thresholds with domain knowledge.

- Level 2: Decomposition in primitive symbols

	Level 1 yields a set of segments that contain music symbols, then this stage aims at further segmenting. The algorigthm will be different with two cases:
	
	- with note head
	- without note head

	and the algorithm has three steps:
	
	1. Stafflines removal with y-projection
	2. High-pass filtering to remove offset
	3. Extraction points computation

<h1 id="2002-1"/>
### Stave Extraction for Printed Music Scores

Detection of staves with dynamic programming (DP), most of descriptions in the paper are related to the detailed implementation and mathematical expressions of DP.

<h1 id="2006-1"/>
### Optical Music Recognition of Early Typographic Prints using Hidden Markov Models

Do recognition without staff removal, but directly detect objects with sliding window and designed features.

<h1 id="2007-1"/>
### A Comparative Survey of Image Binarisation Algorithms for Optical Recognition on Degraded Musical Sources

<h1 id="2007-2"/>
### Handwritten Symbol Recognition by a Boosted Blurred Shape Model with Error Correction

<h1 id="2007-3"/>
### Robust and Adaptive OMR System Including Fuzzy Modeling, Fusion of Musical Rules, and Possible Error Detection

<h1 id="2008-1"/>
### A Comparative Study of Staff Removal Algorithms

The paper aims at describing the methods eliminating staves and the quantitive evaluation of the performance removing staves.

#### Important statements
- The problem can be categorized as a foreground/background classification task
- Deformation techniques because of difficulties to build real ground truths

#### Staff detection

- RLC to obtain stafflines information
- Detect stafflines by finding peaks of horizontal projection at each vertical slices
- Thin the staffsegments by replacing them with their center points
- Link the detected peaks with some defined thresholds

#### Staff removal

- Four categories
	1. Line tracking

		Use thickness thresholding to eliminate stafflines, or some methods compute chord length with respect to a angle parameter.
	
	2. Vector field

		Each pixel is transfromed into 2-D vector, where the values indicate the longest chord length and its corresponded angle.
	
	3. Run-length

		Compute the black/white runs to determine if each consecutive 1's or 0's is a part of a staffline.
	
	4. Skeletonization

		Detect stafflines with skeleton information with some criteria based on domain knowledge.
		
#### Image deformation

| Deformation | Type | Parameter description |
|:------:|:-----:|:------:|
| Resolution | deterministic | dots per inch |
| Rotation | deterministic | rotation angle |
| Curvature | deterministic | height:width ratio of sine curve |
| Typeset emulation | both | gap width, maximal height and variance of vertical shift |
| Line interruptions | random | interruption frequency, maximal width and variance of gap width |
| Thickness variation | random | Markov chain stationary distribution and inertia factor |
| y-variation | random | Markov chain stationary distribution and inertia factor | 
| degradation | random | a degradation model for emulating local distortions suggested by Kanungo et al. |
| white speckles | random | speckle frequency, random walk length and smoothing factor |

#### Error metrices

- Pixel level
- Segmentation region level
- Staffline interruptions
- Methods of statistical analysis

<h1 id="2009-1"/>
### Staff Detection with Stable Paths

<h1 id="2010-1"/>
### An Efficient Staff Removal Approach from Printed Musical Documents

<h1 id="2011-1"/>
### Music Score Binarization Based on Domain Knowledge

<h1 id="2012-1"/>
### Multi-line Fitting Using Two-Stage Iterative Adaptive Approach