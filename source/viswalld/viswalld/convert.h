#include <iostream>
#include <sstream>
#include <string>
#include <stdexcept>

class BadConversion : public std::runtime_error {
public:
	BadConversion(const std::string& s)
		: std::runtime_error(s)
		{ }
};

inline std::string stringify (int x)
{
	std::ostringstream o;
	if (!(o << x))
		throw BadConversion("stringify(int)");
	return o.str();
}
