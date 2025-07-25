"use client"
import React from "react";
import { useState } from "react";
import { loginUser, registerUser } from "../redux/authSlice";
import { useDispatch, useSelector } from "react-redux";
export default function Login(){
  const [signIn, setSignIn] = useState(false);
  const [signUpForm, setSignUpForm] = useState({"username": "", "password": ""})
  const [signInForm, setSignInForm] = useState({"username": "", "password": ""})
  const dispatch = useDispatch()
  const auth = useSelector((state) => state.authentication);
  
  // getting token from local storage

// Sign up
const handleSignUp = async (e) => {
  e.preventDefault();
  const result = await dispatch(registerUser(signUpForm));
  if (registerUser.fulfilled.match(result)) {
    window.location.reload(); // refresh after successful signup
  } else {
    console.error("Sign up failed");
  }
};

// Sign in
const handleSignIn = async (e) => {
  e.preventDefault();
  const result = await dispatch(loginUser(signInForm));
  if (loginUser.fulfilled.match(result)) {
    window.location.reload(); // refresh after successful login
  } else {
    console.error("Login failed");
  }
};
  return(
    <>   
    <div className="flex justify-center">
    {signIn ? 
      // sign in
      (
      <form name="login" onSubmit={handleSignIn} className="flex flex-col border-5 bg-[#2f9e44] w-[100%] h-[80%] border-dashed rounded-xl p-4 gap-3 items-center text-xl">
          <h2 className="text-3xl">Login</h2>
           <input type="text" className="border-2 border-5 outline-none rounded-xl bg-[#40c057]/90 p-3" name="username" placeholder="Name" onChange={(e)=> setSignInForm({...signInForm, username: e.target.value})}/>
           <input type="text" className="border-2 border-5 outline-none rounded-xl bg-[#40c057]/90 p-3" name="password" placeholder="Password" onChange={(e)=> setSignInForm({...signInForm, password: e.target.value})}/>
           <p className="text-lg text-[#b2f2bb]">Do not have an account? <span className="text-white text-lg"><button onClick={()=>setSignIn(false)}>Create an account</button></span> </p>
          <input type="submit" className="bg-[#40c057] border-5 text-lg text-white  w-[50%] rounded-lg" value="SignIn"/>
      </form>):

          // sign up
          (
          <form name="signup" onSubmit={handleSignUp} className="flex flex-col border-5 bg-[#2f9e44] w-[100%] h-[80%] border-dashed rounded-xl p-4 gap-3 items-center text-xl" method="post">
              <h2 className="text-3xl">Sign up</h2>
              <input type="text" className="border-2 border-5 outline-none rounded-xl bg-[#40c057]/90 p-3" name="username" placeholder="Name" onChange={(e)=> setSignUpForm({...signInForm, username: e.target.value})}/>
              <input type="text" className="border-2 border-5 outline-none bg-[#40c057] rounded-xl p-3" name="password" placeholder="Password" onChange={(e)=> setSignUpForm({...signUpForm, password: e.target.value})}/>
               <p className="text-lg text-[#b2f2bb]">Already have an account? <span className="text-white text-xl"><button onClick={()=>setSignIn(true)}>Sign in</button></span> </p>
              <input type="submit" className="bg-[#40c057] border-5 text-lg text-white  w-[50%] rounded-lg" value="SignUp"/>
          </form>
          )
          }
    </div>
  </>
  );  
 }