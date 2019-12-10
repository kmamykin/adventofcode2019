from dataclasses import dataclass
from itertools import groupby
from functools import reduce

@dataclass
class Image:
    width: int
    height: int
    nlayers: int
    data: [str]

    @classmethod
    def decode(cls, width, height, image_data):
        if len(image_data) % (width * height):
            raise Exception('Invalid size of the image data')
        nlayers = len(image_data) // (width * height)
        return Image(width, height, nlayers, image_data)

    def pixel_at(self, layer_idx, h, w):
        return self.data[(layer_idx*self.height*self.width) + (h*self.width) + w]

    def pixels_in_layer(self, layer_idx):
        for h in range(self.height):
            for w in range(self.width):
                yield self.pixel_at(layer_idx, h, w)

    def distribution_of_digits_in_layer(self, layer_idx):
        def reducer(result, e):
            if e in result.keys():
                result[e] = result[e] + 1
            else:
                result[e] = 1
            return result
        return reduce(reducer, self.pixels_in_layer(layer_idx), {})

    def print(self, layer_idx=0):
        for h in range(self.height):
            line_start = (layer_idx*self.height*self.width) + (h*self.width)
            line = self.data[line_start:line_start+self.width]
            print(line.replace('0', u'\u2588').replace('1',' ').replace('2', ' '))

    def merge_layers(self):
        def merge_pixels(pixels):
            for p in pixels:
                if p in ('0', '1'):
                    return p
            return '2'
        merged_data = []
        for h in range(self.height):
            for w in range(self.width):
                pixels = []
                for l in range(self.nlayers):
                    pixels.append(self.pixel_at(l, h, w))
                merged_pixel = merge_pixels(pixels)
                merged_data.append(merged_pixel)
        return Image(self.width, self.height, 1, "".join(merged_data))

input = open("day08/input1.txt").read().strip()
image = Image.decode(25, 6, input)
print(image)
print(image.data)
print("".join(image.pixels_in_layer(0)))
print("".join(image.pixels_in_layer(1)))

print(image.distribution_of_digits_in_layer(0))
print(image.distribution_of_digits_in_layer(1))

def problem1(image):
    cnt = 10000000
    result = 0
    for l in range(image.nlayers):
        dist = image.distribution_of_digits_in_layer(l)
        if dist['0'] < cnt:
            cnt = dist['0']
            result = dist['1'] * dist['2']
    return result, cnt

print(problem1(image))

#Image(2, 2, 4, "0222112222120000").merge_layers().print()

image.merge_layers().print()