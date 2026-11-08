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

# Testfirmware (Anhang A): Kern mit -DFLUIDI_TESTFW=n, eigenes Testprogramm je Variante
TF_SRC  := $(filter-out test_main.c,$(SRC)) $(CORE)/fl_testfw.c test_testfw.c
TF_BINS := $(B)/test_tf1 $(B)/test_tf2 $(B)/test_tf3 $(B)/test_tf4

.PHONY: all run run-tf clean
all: run

$(B)/vectors.h: gen_vectors.py ../../tools/fluidi_proto.py
	@mkdir -p $(B)
	$(PYTHON) gen_vectors.py $@

$(B)/test_fluidi: $(SRC) $(B)/vectors.h $(wildcard $(CORE)/*.h) port_sim.h
	$(CC) $(CFLAGS) $(SRC) -lm -o $@

$(B)/test_tf%: $(TF_SRC) $(B)/vectors.h $(wildcard $(CORE)/*.h) port_sim.h
	$(CC) $(CFLAGS) -DFLUIDI_TESTFW=$* $(TF_SRC) -lm -o $@

run-tf: $(TF_BINS)
	@for n in 1 2 3 4; do ./$(B)/test_tf$$n || exit 1; done
	$(PYTHON) -m unittest discover -s ../../../scripts -p "test_testfw_eval.py" -q

run: $(B)/test_fluidi $(TF_BINS)
	./$(B)/test_fluidi
	@for n in 1 2 3 4; do ./$(B)/test_tf$$n || exit 1; done
	$(PYTHON) -m unittest discover -s ../../../scripts -p "test_testfw_eval.py" -q
	$(PYTHON) -m unittest discover -s ../../../scripts -p "test_flash_sensor.py" -q
	$(PYTHON) -m unittest discover -s ../../tools -p "test_pairing_mitm.py" -q

clean:
	rm -rf $(B)
