# fluidi Sensor-Firmware – Host-Unit-Tests (gcc, Python mit `cryptography`), ohne Hardware
#   make -C firmware/sensor/tests            (oder: make test im Firmware-Ordner)
CC      ?= gcc
PYTHON  ?= python3
B       := build
CORE    := ../core
CFLAGS  := -std=c99 -O1 -g -Wall -Wextra -Werror -Wno-missing-field-initializers -fsanitize=address,undefined \
           -I$(CORE) -I. -I$(B) -DFLUIDI_HW_REV=0x0B
SRC     := $(CORE)/fl_crypto.c $(CORE)/fl_aes_sw.c $(CORE)/fl_proto.c $(CORE)/fl_settings.c $(CORE)/fl_meas.c \
           $(CORE)/fl_ringlog.c $(CORE)/fl_ui.c $(CORE)/fl_ota.c $(CORE)/fl_nvstore.c $(CORE)/fl_app.c port_sim.c test_main.c

.PHONY: all run clean
all: run

$(B)/vectors.h: gen_vectors.py ../../tools/fluidi_proto.py
	@mkdir -p $(B)
	$(PYTHON) gen_vectors.py $@

$(B)/test_fluidi: $(SRC) $(B)/vectors.h $(wildcard $(CORE)/*.h) port_sim.h
	$(CC) $(CFLAGS) $(SRC) -lm -o $@

run: $(B)/test_fluidi
	./$(B)/test_fluidi
	$(PYTHON) -m unittest discover -s ../../../scripts -p "test_flash_sensor.py" -q

clean:
	rm -rf $(B)
