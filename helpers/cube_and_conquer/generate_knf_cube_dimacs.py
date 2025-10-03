import os
import shutil
import argparse

# Create a <num>_dimacsFile.knf for each cube (inefficient but simple) 
def createCubeDimacs():
    template_knf = os.path.join(resultsFolder, "dimacsFile.knf")

    cubes_path   = os.path.join(resultsFolder, "cubes.icnf")

    with open(cubes_path) as cubeFile:
        print(f"Opening cubes file {cubes_path}")
        cubes = [
            line.split('a ')[1].rsplit(' ',1)[0]
            for line in cubeFile
            if line.startswith('a ')
        ]
    print(f"Number of cubes found: {len(cubes)}. Creating cubed KNF dimacsFiles.")

    for i, cube in enumerate(cubes):
        dest = os.path.join(resultsFolder, f"{i}_dimacsFile.knf")

        shutil.copyfile(template_knf, dest) 

        with open(dest, 'a') as out:
            #out.write("\n")
            for lit in cube.split():
                out.write(f"{lit} 0\n")

        lines = open(dest).read().splitlines()
        hdr   = lines[0].split()   # ["p","knf","<vars>","<clauses>"]
        old_c = int(hdr[3])
        new_c = old_c + len(cube.split())
        lines[0] = f"p knf {hdr[2]} {new_c}"
        open(dest, 'w').write('\n'.join(lines))

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f","--folder",
        type=str,
        required=True,
        help="results folder"
    )
    return vars(parser.parse_args())

if __name__ == "__main__":
    args = parse_arguments()
    resultsFolder = args["folder"]
    createCubeDimacs()