cmake_minimum_required(VERSION 2.6)
find_package(PythonInterp REQUIRED)

execute_process(
COMMAND
${PYTHON_EXECUTABLE} -c "from distutils import sysconfig; print sysconfig.get_python_lib(1,0,prefix='${CMAKE_INSTALL_EXEC_PREFIX}')"
OUTPUT_VARIABLE PYTHON_INSTDIR
OUTPUT_STRIP_TRAILING_WHITESPACE
)
file(GLOB pythons RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} *.py)
install(FILES ${pythons} DESTINATION ${PYTHON_INSTDIR}/tek)
add_subdirectory(io)
add_subdirectory(util)
add_subdirectory(config)
add_subdirectory(bin)
