import math
from hashlib import sha256
from hashlib import sha512
from hashlib import blake2b


from const import rawEstimateData, biasData, tresholdData
from compat import *
import hll
import time

def countDistinct(arr): 
  
    s = set() 
    res = 0
    for i in range(len(arr)): 
      
        if (arr[i] not in s): 
            s.add(arr[i]) 
            res += 1
      
    return res

def bit_length(w):
    return w.bit_length()


def bit_length_emu(w):
    return len(bin(w)) - 2 if w > 0 else 0


def get_treshold(p):
    return tresholdData[p - 4]


def estimate_bias(E, p, c):
    bias_vector = biasData[p - 4]
    for i in range(len(bias_vector)):
        bias_vector[i] += c
    nearest_neighbors = get_nearest_neighbors(E, rawEstimateData[p - 4])
    return sum([float(bias_vector[i]) for i in nearest_neighbors]) / len(nearest_neighbors)


def get_nearest_neighbors(E, estimate_vector):
    distance_map = [((E - float(val)) ** 2, idx) for idx, val in enumerate(estimate_vector)]
    distance_map.sort()
    return [idx for dist, idx in distance_map[:6]]


def get_alpha(p):
    if not (4 <= p <= 16):
        raise ValueError("p=%d should be in range [4 : 16]" % p)

    if p == 4:
        return 0.674

    if p == 5:
        return 0.697

    if p == 6:
        return 0.709
    return 0.7213 / (1.0 + 1.079 / (1 << p))


def get_rho(w, max_width):
    rho = max_width - bit_length(w) + 1

    if rho <= 0:
        raise ValueError('w overflow')

    return rho


class HyperLogLog(object):

    __slots__ = ('alpha', 'p', 'm', 'M','hashing_fxn', 'change_bias')

    def __init__(self, error_rate, hashing_fxn, change_bias):
        if not (0 < error_rate < 1):
            raise ValueError("Error_Rate must be between 0 and 1.")

        p = int(math.ceil(math.log((1.04 / error_rate) ** 2, 2)))

        self.change_bias = change_bias
        self.alpha = get_alpha(p)
        self.hashing_fxn = hashing_fxn
        self.p = p
        self.m = 1 << p
        self.M = [ 0 for i in range(self.m) ]

    def __getstate__(self):
        return dict([x, getattr(self, x)] for x in self.__slots__)

    def __setstate__(self, d):
        for key in d:
            setattr(self, key, d[key])

    def add(self, value):

        if(self.hashing_fxn == "sha256"):
            x = long(sha256(bytes(value.encode('utf8') if isinstance(value, unicode) else value)).hexdigest()[:16], 16)
        if(self.hashing_fxn == "sha512"):
            x = long(sha512(bytes(value.encode('utf8') if isinstance(value, unicode) else value)).hexdigest()[:16], 16)
        if(self.hashing_fxn == "blake2b"):
            x = long(blake2b(bytes(value.encode('utf8') if isinstance(value, unicode) else value)).hexdigest()[:16], 16)
        j = x & (self.m - 1)
        w = x >> self.p

        self.M[j] = max(self.M[j], get_rho(w, 64 - self.p))

    def __eq__(self, other):
        if self.m != other.m:
            raise ValueError('Counters precisions should be equal')

        return self.M == other.M

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return round(self.card())

    def _Ep(self):
        E = self.alpha * float(self.m ** 2) / sum(math.pow(2.0, -x) for x in self.M)
        return (E - estimate_bias(E, self.p, self.change_bias)) if E <= 5 * self.m else E

    def card(self):
        V = self.M.count(0)

        if V > 0:
            H = self.m * math.log(self.m / float(V))
            return H if H <= get_treshold(self.p) else self._Ep()
        else:
            return self._Ep()
def main():
    max = 10
    hll_hashing = "sha256"
    changeBias = 0
    for i in range(0,7):

        for j in range(1,2):

            if(max < 100):
                change_bias = -1.5
                hashing = "blake2b"
            if(max > 100 and max <=10000):
                change_bias = 0.5
                hashing = "sha256"
            if(max > 10000):
                hashing = "sha512"
                change_bias = 0.1
            file_name = str(max) + "data" + str(j) +".txt"
            start1 = time.time()
            f=open(file_name, "r")
            content = f.read()
            
            num = content.split('\n')
            num.remove('')
            
            x1 = countDistinct(num)
            end1 = time.time()
            
            hyLog = hll.HyperLogLog()
            for n in num:
                hyLog.add(n)
            start = time.time() 
            x = hyLog.card()
            end = time.time()

            

            hyLog_mod = HyperLogLog(0.01, hll_hashing, changeBias)
            for n in num:
                hyLog_mod.add(n)
            start_mod = time.time() 
            x_mod = hyLog_mod.card()
            end_mod = time.time()

            print(hyLog.p, hyLog.m)
            print("\n")
            print("*************************************************")
            print("File Name - ",file_name)
            print("Number of Entries - ",max)
            print("\n")
            print("Brute Force - ")
            print("Cardinality: ",x1,"\tTimeTaken: ",(end1-start1)*1000)
            print("\n")
            print("Original  HLL - ")
            print("Cardinality: ",x,"\tTimeTaken: ",(end-start)*1000,"\nAccuracy: ",100-(abs(x-x1)/x1)*100)
            print("\n")
            print("Modified HLL - ")
            print("Cardinality: ",x_mod,"\tTimeTaken: ",(end_mod-start_mod)*1000,"\nAccuracy: ",100-(abs(x_mod-x1)/x1)*100)
            print("*************************************************")
            print("\n")
        max *= 10


if __name__ == '__main__':
    main()
