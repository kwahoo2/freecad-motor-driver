CC=g++
CFLAGS=-I. -pthread -lpigpio -lrt
DEPS = bresenham.h pigpio_driver.h
OBJ = udp_receiver.o bresenham.o pigpio_driver.o

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

udp_receiver: $(OBJ)
	$(CC) -o $@ $^ $(CFLAGS)
