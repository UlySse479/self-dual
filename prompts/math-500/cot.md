Give your final answer by `\boxed{answer}`.

Question: Kevin Kangaroo begins hopping on a number line at 0. He wants to get to 1, but he can hop only $\frac{1}{3}$ of the distance. Each hop tires him out so that he continues to hop $\frac{1}{3}$ of the remaining distance. How far has he hopped after five hops? Express your answer as a common fraction.
Answer: Let's think step by step
Kevin hops $1/3$ of the remaining distance with every hop.
His first hop takes $1/3$ closer.
For his second hop, he has $2/3$ left to travel, so he hops forward $(2/3)(1/3)$.
For his third hop, he has $(2/3)^2$ left to travel, so he hops forward $(2/3)^2(1/3)$.
In general, Kevin hops forward $(2/3)^{k-1}(1/3)$ on his $k$th hop.
We want to find how far he has hopped after five hops.
This is a finite geometric series with first term $1/3$, common ratio $2/3$, and five terms.
Thus, Kevin has hopped $\frac{\frac{1}{3}\left(1-\left(\frac{2}{3}\right)^5\right)}{1-\frac{2}{3}} = \frac{211}{243}$. The answer is $\boxed{\frac{211}{243}}$.


Question: What is the area of the region defined by the equation $x^2+y^2 - 7 = 4y-14x+3$?
Answer: Let's think step by step
We rewrite the equation as $x^2 + 14x + y^2 - 4y = 10$ and then complete the square,
resulting in  $(x+7)^2-49 + (y-2)^2-4=10$,
or $(x+7)^2+(y-2)^2=63$.
This is the equation of a circle with center $(-7, 2)$ and radius $\sqrt{63},$
so the area of this region is $\pi r^2 = 63\pi$. The answer is $\boxed{63\pi}$.


Question: If $x^2+y^2=1$, what is the largest possible value of $|x|+|y|$?
Answer: Let's think step by step
If $(x,y)$ lies on the circle,
so does $(x,-y),$ $(-x,-y),$ and $(-x,-y),$ (which all give the same value of $|x| + |y|$),
so we can assume that $x \ge 0$ and $y \ge 0.$
Then $|x| + |y| = x + y.$  Squaring, we get
\[(x + y)^2 = x^2 + 2xy + y^2 = 1 + 2xy.\]
Note that $(x - y)^2 \ge 0.$
Expanding, we get $x^2 - 2xy + y^2 \ge 0,$ so $2xy \le x^2 + y^2 = 1.$
Hence,\[1 + 2xy \le 2,\]which means $x + y \le \sqrt{2}.$
Equality occurs when $x = y = \frac{1}{\sqrt{2}},$
so the maximum value of $|x| + |y|$ is $\sqrt{2}.$ The answer is $\boxed{\sqrt{2}}$.


Question: If $f(x)=\frac{ax+b}{cx+d}, abcd\not=0$ and $f(f(x))=x$ for all $x$ in the domain of $f$, what is the value of $a+d$?
Answer: Let's think step by step
The condition $f(f(x))$ means that $f$ is the inverse of itself,
so its graph is symmetrical about the line $y = x$.
With a rational function of this form, we will have two asymptotes:
a vertical one at $x=-d/c$ if $cx+d$ does not divide $ax+b$,
and a horizontal one at $y=a/c$,
if we take the limit of $f(x)$ as $x$ goes to $\pm\infty$.
In order for $f$ to be its own inverse, the intersection of the asymptotes must lie on the line $y=x$
so that it and its asymptotes reflect onto themselves.
This means that $-d/c=a/c$,
and therefore $-d=a$ and $a+d=0$. The answer is $\boxed{0}$.


Question: A math teacher requires Noelle to do one homework assignment for each of the first five homework points she wants to earn; for each of the next five homework points, she needs to do two homework assignments; and so on, so that to earn the $n^{\text{th}}$ homework point, she has to do $n\div5$ (rounded up) homework assignments. For example, when she has 11 points, it will take $12\div5=2.4\rightarrow3$ homework assignments to earn her $12^{\text{th}}$ point. What is the smallest number of homework assignments necessary to earn a total of 25 homework points?
Answer: Let's think step by step
Noelle only has to do 1 homework assignment to earn her first point,
and the same is true for each of her first five points.
She must then do 2 homework assignments to earn her sixth point, seventh point, and so on, up to her tenth point.
Continuing, we see that Noelle must do a total of \[1+1+1+1+1+2+2+2+2+2+\dots+5+5+5+5+5\] homework assignments to earn 25 points.
This sum may be rewritten as $5(1+2+3+4+5)=5(15)=75$. The answer is $\boxed{75}$.


Question: The quadratic equation $x^2+mx+n=0$ has roots that are twice those of $x^2+px+m=0,$ and none of $m,$ $n,$ and $p$ is zero. What is the value of $n/p?$
Answer: Let's think step by step
Let $r_1$ and $r_2$ be the roots of $x^2+px+m=0.$
Since the roots of $x^2+mx+n=0$ are $2r_1$ and $2r_2,$ we have the following relationships: \[
m=r_1 r_2,\quad n=4r_1 r_2,\quad p=-(r_1+r_2), \quad\text{and}\quad
m=-2(r_1+r_2).
\] So \[
n = 4m, \quad p = \frac{1}{2}m,
\quad\text{and}\quad
\frac{n}{p}=\frac{4m}{\frac{1}{2}m}=8.
\]
Alternatively, the roots of \[
\left(\frac{x}{2}\right)^2 + p\left(\frac{x}{2}\right) + m = 0
\] are twice those of $x^2 + px + m = 0.$
Since the first equation is equivalent to $x^2 + 2px + 4m = 0,$
we have \[m = 2p \quad\text{and}\quad n = 4m, \quad\text{so}\quad \frac{n}{p} = 8.\] The answer is $\boxed{8}$.


Question: Expand $(2z^2 + 5z - 6)(3z^3 - 2z + 1)$.
Answer: Let's think step by step
$$\begin{array}{crrrrrrr}
& & & 3z^3 & & -2z & + 1 & \\
\times & & & & 2z^2 & +5z & -6 \\
\cline{1-7}\rule{0pt}{0.17in}
& & & -18z^3 & & +12z & -6 & \\
& & +15z^4 & & -10z^2 & +5z & & \\
+ & 6z^5 & & -4z^3 & +2z^2 & & & \\
\cline{1-7}\rule{0pt}{0.17in}
& 6z^5 & +15z^4 & -22z^3 & - 8z^2 &+17z & -6 &
\end{array}. The answer is $\boxed{6z^5+15z^4-22z^3-8z^2+17z-6}$.


Question: Find the mean of all solutions for $x$ when $x^3 + 3x^2 - 10x = 0$.
Answer: Let's think step by step
First, we factor the equation as $x(x^2 +3x - 10) = 0$.
So, one solution is $x=0$ and the other two solutions are the solutions to $x^2 + 3x-10=0$.
We could either factor the quadratic, or note that the sum of the solutions to this quadratic is $-(3/1)=-3$,
so the mean of the three solutions to the original equation is $-3/3=-1$. The answer is $\boxed{-1}$.