#include <iostream>
#include <map>
using namespace std;

int main(){
    string s;
    map<string, int> bag;
    while (cin >> s){
        if (s == "minimum?"){
            if (bag.empty()){
                cout << "indefinite minimum" << endl;
            } else {
                cout << "minimum: " << bag.begin() -> first << ", " << bag.begin() -> second << " time(s)" << endl;
            }
        }
        if (s == "maximum?"){
            if (bag.empty()){
                cout << "indefinite maximum" << endl;
            } else {
                map<string, int>::iterator it = bag.end();
                --it;
                cout << "maximum: " << it -> first << ", " << it -> second << " time(s)" << endl;
            }
        }
        if (s == "store"){
            string word;
            cin >> word;
            if (not bag.count(word)){
                bag.insert({word, 1});
            } else {
                map<string, int>::iterator it = bag.find(word);
                it -> second += 1;
            }
        }
        if (s == "delete"){
            string word;
            cin >> word;
            if (bag.find(word) != bag.end()){
                map<string, int>::iterator it = bag.find(word);
                it -> second -= 1;
                if (it -> second == 0){
                    bag.erase(word);
                }
            }
        }
    }
}