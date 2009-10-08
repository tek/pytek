cmake_minimum_required(VERSION 2.6)
find_package(PythonInterp REQUIRED)

execute_process(
COMMAND
${PYTHON_EXECUTABLE} -c "from distutils import sysconfig; print sysconfig.get_python_lib(1,0,prefix='${CMAKE_INSTALL_EXEC_PREFIX}')"
OUTPUT_VARIABLE PYTHON_INSTDIR
OUTPUT_STRIP_TRAILING_WHITESPACE
)
install(FILES __init__.py process.py config.py debug.py errors.py tools.py
	user_input.py command_line.py terminal.py
	DESTINATION ${PYTHON_INSTDIR}/tek)
