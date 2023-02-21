
from PIL import Image
import os


player = "Car_classic_red_complete"
base = "/mnt/c/Users/Zack/Documents/unity/Assets/modernexteriors-win/Modern_Exteriors_16x16/Animated_16x16/Vehicles_16x16/Cars_16x16"
#base = "/mnt/c/Users/Zack/Documents/unity/Assets/moderninteriors-win/LimeZu Character Generator Release 1.1.5/Saved Characters"
file = base+"/"+player+".png"
img = Image.open(file)

os.mkdir(f"{base}/{player}")

types = ["overview", "idle", "walk", "sleep", "sit1", "sit2", "phone", "read", "push_cart", "pick_up", "gift", "lift", "throw", "hit", "punch", "stab", "grab_gun", "gun_idle", "shoot", "hurt"]

def getFrames(animation):
	if animation == "overview":
		return 1
	elif animation in ["shoot", "hurt"]:
		return 3
	elif animation == "grab_gun":
		return 4
	elif animation in ["idle", "walk", "sit1", "sit2", "push_cart", "hit", "punch", "gun_idle"]:
		return 6
	elif animation in ["gift"]:
		return 10
	return 0

dirs = ["right", "up", "left", "down"]
width = 896

left = 0
top = 0
right = 16
for animation in types:
	frames = getFrames(animation)

	newImg = img.crop((0, top, width, top+32))
	newImg.save(f"{base}/{player}/{animation}.png")
	top += 32
