#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2017 Yorik van Havre <yorik@uncreated.net>              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

# Luxrender renderer for FreeCAD

# This file can also be used as a template to add more rendering engines.
# You will need to make sure your file is named with a same name (case sensitive)
# That you will use everywhere to describe your renderer, ex: Appleseed or Povray


# A render engine module must contain the following functions:
#
#    writeCamera(por,rot,up,target): returns a string containing an openInventor camera string in renderer format
#    writeObject(view,mesh,color,alpha): returns a string containing a RaytracingView object in renderer format
#    render(project,prefix,external,output,width,height): renders the given project, external means
#                                                         if the user wishes to open the render file
#                                                         in an external application/editor or not. If this
#                                                         is not supported by your renderer, you can simply
#                                                         ignore it
#
# Additionally, you might need/want to add:
#
#    Preference page items, that can be used in your functions below
#    An icon under the name Renderer.svg (where Renderer is the name of your Renderer


import FreeCAD
import math
import os
import re
import tempfile


def writeCamera(pos,rot,up,target):

    # this is where you create a piece of text in the format of
    # your renderer, that represents the camera.

    pos = str(pos.x) + " " + str(pos.y) + " " + str(pos.z)
    target = str(target.x) + " " + str(target.y) + " " + str(target.z)
    up = str(up.x) + " " + str(up.y) + " " + str(up.z)

    cam  = "# declares position and view direction\n"
    cam += "# Generated by FreeCAD (http://www.freecadweb.org/)\n"
    cam += "LookAt " + pos + " "
    cam += target + " "
    cam += up + "\n"
    return cam


def writeObject(viewobj,mesh,color,alpha):

    # This is where you write your object/view in the format of your
    # renderer. "obj" is the real 3D object handled by this project, not
    # the project itself. This is your only opportunity
    # to write all the data needed by your object (geometry, materials, etc)
    # so make sure you include everything that is needed


    objdef = ""
    objname = viewobj.Name

    # format color
    color = str(color[0])+" "+str(color[1])+" "+str(color[2])

    P = ""
    N = ""
    tris = ""
    for v in mesh.Topology[0]:
        P += str(v.x) + " " + str(v.y) + " " + str(v.z) + " "
    for n in mesh.getPointNormals():
        N += str(n.x) + " " + str(n.y) + " " + str(n.z) + " "
    for t in mesh.Topology[1]:
        tris += str(t[0]) + " " + str(t[1]) + " " + str(t[2]) + " "

    # write shader

    objdef += "MakeNamedMaterial \"" + objname + "_mat\"\n"
    objdef += "    \"color Kd\" [" + color + "]\n"
    objdef += "    \"float sigma\" [0.2]\n"
    objdef += "    \"string type\" [\"matte\"]\n"
    if alpha < 1.0:
        objdef += "    \"float transparency\" [\""+str(alpha)+"\"]\n"
    objdef += "\n"

    # write mesh

    objdef += "AttributeBegin #  \"" + objname + "\"\n"
    objdef += "Transform [1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1]\n"
    objdef += "NamedMaterial \"" + objname + "_mat\"\n"
    objdef += "Shape \"mesh\"\n"
    objdef += "    \"integer triindices\" [" + tris + "]\n"
    objdef += "    \"point P\" [" + P + "]\n"
    objdef += "    \"normal N\" [" + N + "]\n"
    objdef += "    \"bool generatetangents\" [\"false\"]\n"
    objdef += "    \"string name\" [\"" + objname + "\"]\n"
    objdef += "AttributeEnd # \"\"\n"

    return objdef


def render(project,prefix,external,output,width,height):

    # here you trigger a render by firing the renderer
    # executable and passing it the needed arguments, and
    # the file it needs to render

    # change image size in template
    f = open(project.PageResult,"r")
    t = f.read()
    f.close()
    res = re.findall("integer xresolution",t)
    if res:
        t = re.sub("\"integer xresolution\".*?\[.*?\]","\"integer xresolution\" ["+str(width)+"]",t)
    res = re.findall("integer yresolution",t)
    if res:
        t = re.sub("\"integer yresolution\".*?\[.*?\]","\"integer yresolution\" ["+str(height)+"]",t)
    if res:
        fp = tempfile.mkstemp(prefix=project.Name,suffix=os.path.splitext(project.Template)[-1])[1]
        f = open(fp,"w")
        f.write(t)
        f.close()
        project.PageResult = fp
        os.remove(fp)
        FreeCAD.ActiveDocument.recompute()

    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Render")
    if external:
        rpath = p.GetString("LuxRenderPath","")
        args = p.GetString("LuxParameters","")
    else:
        rpath = p.GetString("LuxConsolePath","")
        args = p.GetString("LuxParameters","")
    if not rpath:
        FreeCAD.Console.PrintError("Unable to locate renderer executable. Please set the correct path in Edit -> Preferences -> Render")
        return
    if args:
        args += " "
    FreeCAD.Console.PrintMessage(prefix+rpath+" "+args+project.PageResult+"\n")
    os.system(prefix+rpath+" "+args+project.PageResult)
    return


