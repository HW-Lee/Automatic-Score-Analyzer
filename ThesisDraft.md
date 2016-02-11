# Automatic Scores Recognition with Divide and Conquer 分治法概念的自動樂譜辨識

## Abstract
TBC

## 1. Introduction
### 1-1. Motivation
In the era full of high-tech tools, most of tasks can be done by computers: people write articles with computers; people draw diagrams with computers; people, of course, design programs with computers. Among various instances we use computers for, one of them is music composition. For purposes of storing and visualising musicians' creation, the score, which contains lots of music information showing how a piece of melody should be played, has been widely used for hundreds of years. However, the score was designed for human beings rather than computers, most of scores are stored as images, which are just sets of pixels and mean nothing for computers. As a result, a field, namely Optical Music Recognition (OMR), discussing methods for letting computers recognize all stuffs illustrated in an image was emphasised.

### 1-2. The Goal
The project aims at developing a framework that enables people to analyze scores programmatically. 

### 1-3. System Design
TBC

### 1-4. Divide and Conquer
#### 1-4-1. What is divide and conquer?
![Concepts of D&C](./ThesisDraft-src/DnC.png)
The figure shows the main concepts of "divide and conquer".  D&C (Divide and Conquer) is an algorithm design paradigm that breaks a complex problem into a couple of relatively simple subproblems, called "divide", then solves them respectively, called "conquer" instead of dealing with it directly. Before conquering, the problem will be divided recursively until it is simple enough to be processed. Finally, the solutions to the subproblems will be merged as those to the original problem.

#### 1-4-2. The way dividing and conquering
In a score, a song is composed of staves, a staff contains measures, which can be regarded as a smallest unit to be recognised. Due to its hierarchical structure, scores recognition is a suitable problem that can be solved with D&C algorithm.
![](./ThesisDraft-src/divide_impl.png)
In the system, a measure is determined as the simplest subproblem to be solved. After binarization, staves are extracted from the binary matrix, and all measures within each staff are extracted respectively. Subsequently, the extracted measures are processed with the recognition system.

#### 1-4-3. Advantages
The main concept of D&C is to simplify problems such that a difficult problem can be turned into many tiny problems. In this way, it brings us some advantages:

- Difficulty of problems

	Due to characteristics of D&C, all problems that can be accurately split are expected to be solved. For this project, if the function detecting staves and measures is reliable, then we can analyze arbitrarily complicated scores.

- Independence of subproblems
	
	A score contains not just all information of the creation, but other noisy things such as metadata of the song, lyrics, and printed defects. By partitioning the original images into pieces of sub-image that contains only one measure, noisy information can be decreased and interference between staves is eliminated. Therefore, the detection tasks are independent with different staves.
	
- Recognition system development

	With single measure images as development set, the recognition system needs to be focused only on how to find symbols in a measure, and the conquer function is simpler.
	
- Parallelism

	Nowadays, a processor usually has multiple cores, and lots of computational tasks are implemented to be executed with parallel programs. In D&C algorithm, the functions solving split subproblems are identically designed. With high independency and similar operations between subproblems, it is a good strategy to process them simultaneously. In other word, the original problem is suitable to be solved with SIMD (Single-Instruction-Multiple-Data) parallel programs.

### 1-5. Applications
TBC

### 1-6. Design of Dissertation
TBC

## 2. Review of Related Research
### 2-1. Binarization

### 2-2. Staff Detection

### 2-3. Staff Removal

## 3. Technical Background
TBC

## 4. Software Framework
TBC

## 5. Results
TBC

## 6. Conclusions
TBC

## 7. References
