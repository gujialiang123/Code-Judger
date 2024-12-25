#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#define N 100020
using namespace std;

int a[N];

int main(void)
{
    int n, m;
    int i;
    long long o;

    freopen("in.txt","r",stdin);
    freopen("out.txt","w",stdout);

    scanf("%d %d", &n, &m);
    for(i = a[0] = 1, o = 0; i <= m; i ++)
    {
        scanf("%d", &a[i]);
        o += (a[i] - a[i - 1] + n) % n;
    }

    printf("%lld\n", o);

    return 0;
}