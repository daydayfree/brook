---
layout: post
title: Binary Tree Maximum Node
---

从现在开始每天做一道练习题。

LintCode link: [http://www.lintcode.com/en/problem/binary-tree-maximum-node/](http://www.lintcode.com/en/problem/binary-tree-maximum-node/)

```c
#include <stdio.h>

typedef struct TreeNode TreeNode;

struct TreeNode
{
    int value;
    TreeNode *left;
    TreeNode *right;
};

TreeNode *max_node(TreeNode *a, TreeNode *b)
{
    if (a == NULL) {
        return b;
    }

    if (b == NULL) {
        return a;
    }

    if (a->value > b->value) {
        return a;
    }

    return b;
}

TreeNode *search_max_node(TreeNode *root)
{
    if (root == NULL) {
        return root;
    }

    TreeNode *l = search_max_node(root->left);
    TreeNode *r = search_max_node(root->right);

    return max_node(root, max_node(l, r));
}

int main(void)
{
    TreeNode root = {.value = 2};
    TreeNode right = {.value = 6};
    TreeNode left = {.value = 5};
    TreeNode left1 = {.value = 7};

    root.left = &left;
    root.right = &right;
    left.left = &left1;

    TreeNode *result = search_max_node(&root);
    printf("Max tree node value = %d \n", result->value);
}

```

输出：

```bash
Max tree node value = 7
```

参考链接： [struct (C programming language)](https://en.wikipedia.org/wiki/Struct_(C_programming_language))

