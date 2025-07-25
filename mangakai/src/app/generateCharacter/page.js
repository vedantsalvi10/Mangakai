"use client"
import { useState,useEffect, useCallback, useRef } from "react";
import { animeConversion, posesGeneration} from "../redux/authSlice";
import { useRouter } from "next/navigation";
import { Toaster } from 'react-hot-toast';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import { useDropzone } from "react-dropzone";
import Skeleton from "react-loading-skeleton";
import { useDispatch,useSelector } from "react-redux";

const CharacterCreation = ()=>{
  const [selectedFile, setSelectedFile] = useState(null)
  const dispatch = useDispatch()
   const router = useRouter()
  const animefy = useSelector((state)=> state.authentication)
  // to handle the image upload for  character generation
const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
    }
  }, []);

const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "image/*": []
    }
  });

  const fileInputRef = useRef();

const handleClick = () => {
  fileInputRef.current?.click();
};
useEffect(() => {
  if (!selectedFile) return;
    const form = new FormData();
    form.append("image", selectedFile);
    dispatch(animeConversion(form));
}, [selectedFile]);

  // handle the log out of the user  
  const handleLogout = () => {
  localStorage.removeItem("token");
  // redirect to login or homepage
  window.location.href = "/";
  };
const generatePoses = ()=>{
  dispatch(posesGeneration())
}
  return(
    <>
     <Toaster position="top-right" />

    <section className="p-8 bg-[url(/anime-style-mythical-dragon-creature.jpg)] flex justify-center items-center w-full h-screen bg-cover bg-center bg-no-repeat">
      
      <div className="bg-white/30 w-[1980px] h-[700px] rounded-2xl flex flex-col items-center">
        
            <div className="flex w-[100%] h-[20%] justify-center">
              {animefy.loading && 
                     <div className="w-[10%]">
                         <DotLottieReact
                   src="https://lottie.host/ae57be7c-b080-49bf-bdcf-a292dd7d9dac/F275oCskAs.lottie"
                   loop
                   autoplay
                 />
            </div>}
             <div className=" h-[100%] w-[80%] flex justify-center items-center">
                <p className=" bg-[#2f9e44] p-5 w-[70%] flex justify-center rounded-xl text-5xl">Create Your own Character</p>
             </div>
             <div className="w-[10%] h-full flex items-center justify-center">
               <button className=" bg-[#2f9e44] p-2 pl-4 pr-4  text-white border-white border-4 rounded-xl text-lg " onClick={handleLogout}>logout</button>
             </div>
      </div>
             <div className="flex justify-center h-[80%] w-[100%] gap-20">
                    <div className="h-[90%] w-[50%] items-center flex flex-col  gap-10">
                     <div className="flex w-full gap-5 justify-center">
                    <button  className="bg-[#2f9e44] text-white border-white [30%] p-2 pl-3 pr-3 border-4 rounded-xl text-lg "  onClick={()=>{router.push("/")}}>Home</button>
                    <button  className="bg-[#40c057]/70 text-white border-white/70 w-[40%] p-2 border-4 rounded-xl text-lg " disabled onClick={()=>{router.push("/generateCharacter")}}>Character Generator</button>
                    {animefy.anime_image && 
                    <button  className="bg-[#2f9e44] text-white border-white  w-[30%] p-2 border-4 rounded-xl text-lg "  onClick={()=>{router.push("/generatePanel")}}>Panel Generator</button>
                     }
                    </div>
                    <div  className="bg-[#2f9e44] w-full p-4 h-[70%] rounded-xl border-dashed border-4 flex flex-col items-center justify-center">
                      
                      <div {...getRootProps()} className="flex items-center flex-col">
                        <input {...getInputProps()} />
                      <img className="w-[50px]" src="/folder.png" />
                      <div className="text-xl mb-2 text-white/70">{selectedFile ? selectedFile.name : "Drop image"}</div>
                      </div>
                       <input ref={fileInputRef} type="file" onChange={(e) => setSelectedFile(e.target.files[0])} className="hidden"/>                   
                         
                         <button type="button" className="bg-[#40c057] w-25 rounded-lg border-4 text-lg text-white" onClick={handleClick}>upload</button>
                         
                    </div>
                   
                    </div>
                      {animefy.anime_image && 
                       <div className="flex flex-col gap-10 w-[20%]  h-[100%] rounded-2xl">
                         <img className="rounded-2xl w-full h-[70%] object-cover" src={animefy.anime_image} alt="user image" />
                          <button className="bg-[#2f9e44] p-4 border-5 rounded-xl text-xl " onClick={generatePoses}>Confirm your Character</button>
                       </div>
                      }
             </div>
      </div>
    </section>
    </>
  );
}

export default CharacterCreation;