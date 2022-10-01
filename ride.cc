/*
ID: chaozch1
TASK: ride
LANG: C++                 
*/
#include <iostream>
#include <fstream>
#include <string>

using namespace std;

int main() {
    ofstream fout("ride.out");
    ifstream fin("ride.in");
    
    string str[2];
    int ans[2] = {1, 1};

    fin >> str[0] >> str[1];

    for (int i = 0; i < 2; i++) {
        for (auto &ch : str[i]) {
            ans[i] *= ch - 'A' + 1;
        }
    }

    fout << (ans[0] % 47 == ans[1] % 47 ? "GO" : "STAY") << endl;

    return 0;
}