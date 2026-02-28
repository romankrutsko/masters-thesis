# Extracted from Ch04.py (Q12 visualization)

import numpy as np
import matplotlib.pyplot as plt


def Power3(x, a):
    return x**a

x = np.arange(1, 11, 1)
y = Power3(x,2)

fig = plt.figure()
fig.add_subplot(2, 2, 1)
plt.scatter(x, y)
plt.title('log(x^2) vs x')
plt.xlabel('x')
plt.ylabel('log(x^2)')

ax = fig.add_subplot(2, 2, 2)
ax.set_xscale('log')
plt.scatter(x, y)
plt.title('log(x^2) vs x on xlog-scale')
plt.xlabel('x')
plt.ylabel('log(x^2)')

ax = fig.add_subplot(2, 2, 3)
ax.set_yscale('log')
plt.scatter(x, y)
plt.title('log(x^2) vs x on ylog-scale')
plt.xlabel('x')
plt.ylabel('log(x^2)')

ax = fig.add_subplot(2, 2, 4)
ax.set_xscale('log')
ax.set_yscale('log')
plt.scatter(x, y)
plt.title('log(x^2) vs x on xylog-scale')
plt.xlabel('x')
plt.ylabel('log(x^2)')
