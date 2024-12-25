#include<bits/stdc++.h>
using namespace std;
const int MAXN=1e5;
int main()
{
	freopen("in.txt","w",stdout);
	srand(time(NULL));
	int n=rand()*rand()%MAXN,m=rand()*rand()%MAXN;
	cout<<n<<" "<<m<<endl;
	while(m--)
		cout<<rand()*rand()%n+1<<" ";
	return 0;
}