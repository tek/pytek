file(GLOB pythons RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} *.py)
install(FILES ${pythons} DESTINATION ${PYTHON_INSTDIR}/tek/io)
